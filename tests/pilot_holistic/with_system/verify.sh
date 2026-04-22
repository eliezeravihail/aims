#!/usr/bin/env bash
# Full end-to-end verification. Exits 0 iff every assertion passes.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
export CONTACTS_DIR="$WORK"

PY="python3 $HERE/contacts.py"
FAIL=0

assert_eq() {
    # $1 = label, $2 = expected, $3 = actual
    if [ "$2" != "$3" ]; then
        echo "FAIL: $1"
        echo "  expected: $2"
        echo "  actual:   $3"
        FAIL=$((FAIL+1))
    else
        echo "ok: $1"
    fi
}

assert_contains() {
    if ! echo "$3" | grep -qF "$2"; then
        echo "FAIL: $1"
        echo "  expected to contain: $2"
        echo "  actual: $3"
        FAIL=$((FAIL+1))
    else
        echo "ok: $1"
    fi
}

assert_rc() {
    if [ "$2" != "$3" ]; then
        echo "FAIL: $1 (rc expected $2, got $3)"
        FAIL=$((FAIL+1))
    else
        echo "ok: $1 (rc=$3)"
    fi
}

# 1. list on missing file => empty
OUT="$($PY list)"; RC=$?
assert_rc "list: missing file does not crash" 0 $RC
assert_eq "list: missing file prints (no contacts)" "(no contacts)" "$OUT"

# 2. find on missing file => no matches
OUT="$($PY find alice)"; RC=$?
assert_rc "find: missing file does not crash" 0 $RC
assert_eq "find: missing file prints (no matches)" "(no matches)" "$OUT"

# 3. remove on missing file => invalid id
OUT="$($PY remove 1 2>&1)"; RC=$?
assert_rc "remove: missing contact => rc 2" 2 $RC
assert_contains "remove: missing contact message" "no contact with id 1" "$OUT"

# 4. add basic
OUT="$($PY add Alice alice@example.com)"; RC=$?
assert_rc "add: basic rc 0" 0 $RC
assert_contains "add: prints id 1" "[1] Alice" "$OUT"

# 5. add with phone
OUT="$($PY add Bob bob@example.com --phone 555-1234)"; RC=$?
assert_rc "add: with phone rc 0" 0 $RC
assert_contains "add: prints id 2" "[2] Bob" "$OUT"
assert_contains "add: phone present" "phone=555-1234" "$OUT"

# 6. duplicate email rejected (case-insensitive)
OUT="$($PY add Eve ALICE@example.com 2>&1)"; RC=$?
assert_rc "add: duplicate email rc 2" 2 $RC
assert_contains "add: duplicate email message" "duplicate email" "$OUT"

# 7. list shows both, sorted by id
OUT="$($PY list)"
EXPECTED="[1] Alice <alice@example.com>
[2] Bob <bob@example.com>  phone=555-1234"
assert_eq "list: shows both" "$EXPECTED" "$OUT"

# 8. find by name
OUT="$($PY find alice)"
assert_contains "find: hits alice" "[1] Alice" "$OUT"

# 9. find by phone substring
OUT="$($PY find 555)"
assert_contains "find: hits by phone" "[2] Bob" "$OUT"

# 10. find with no match
OUT="$($PY find zzz)"
assert_eq "find: no match" "(no matches)" "$OUT"

# 11. update name
OUT="$($PY update 1 --name Alicia)"; RC=$?
assert_rc "update: rc 0" 0 $RC
assert_contains "update: new name appears" "Alicia" "$OUT"

# 12. update to duplicate email rejected
OUT="$($PY update 1 --email bob@example.com 2>&1)"; RC=$?
assert_rc "update: dup email rc 2" 2 $RC
assert_contains "update: dup email message" "duplicate email" "$OUT"

# 13. update invalid id
OUT="$($PY update 999 --name x 2>&1)"; RC=$?
assert_rc "update: invalid id rc 2" 2 $RC
assert_contains "update: invalid id message" "no contact with id 999" "$OUT"

# 14. update with non-numeric id
OUT="$($PY update abc --name x 2>&1)"; RC=$?
assert_rc "update: non-numeric id rc 2" 2 $RC
assert_contains "update: non-numeric id message" "invalid id" "$OUT"

# 15. remove id 1
OUT="$($PY remove 1)"; RC=$?
assert_rc "remove: rc 0" 0 $RC
assert_contains "remove: message" "removed [1]" "$OUT"

# 16. remove again => invalid id
OUT="$($PY remove 1 2>&1)"; RC=$?
assert_rc "remove: second time rc 2" 2 $RC

# 17. CRITICAL: next add gets id 3, not 1 (strict monotonic)
OUT="$($PY add Carol carol@example.com)"; RC=$?
assert_rc "add after remove: rc 0" 0 $RC
assert_contains "add after remove: id is 3 (monotonic)" "[3] Carol" "$OUT"

# 18. remove a middle id and confirm counter still advances
$PY add Dave dave@example.com > /dev/null         # id 4
$PY add Erin erin@example.com > /dev/null         # id 5
$PY remove 3 > /dev/null                           # remove Carol
$PY remove 4 > /dev/null                           # remove Dave
OUT="$($PY add Frank frank@example.com)"
assert_contains "add after 2 removes: id is 6" "[6] Frank" "$OUT"

# 19. persistence across runs: Bob (2), Erin (5), Frank (6) present; 1/3/4 gone
OUT="$($PY list)"
assert_contains "persist: Bob present (id 2 never removed)" "[2] Bob" "$OUT"
assert_contains "persist: Erin present" "[5] Erin" "$OUT"
assert_contains "persist: Frank present" "[6] Frank" "$OUT"
for gone in 1 3 4; do
    if echo "$OUT" | grep -qE "^\[${gone}\] "; then
        echo "FAIL: persist: removed id $gone should not reappear"
        FAIL=$((FAIL+1))
    else
        echo "ok: persist: id $gone does not reappear"
    fi
done

# 20. storage is plain text (not binary/json/sqlite)
#     Use a pure Python check: every byte must be printable ASCII or whitespace.
python3 - "$WORK/contacts.tsv" "$WORK/contacts.counter" <<'PYEOF'
import sys
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        data = f.read()
    for b in data:
        if not (32 <= b < 127 or b in (9, 10, 13)):
            print(f"FAIL: non-printable byte {b} in {path}")
            sys.exit(1)
    print(f"ok: plain text: {path}")
PYEOF
if [ $? -ne 0 ]; then FAIL=$((FAIL+1)); fi

# 21. add with missing required args
OUT="$($PY add 2>&1)"; RC=$?
if [ "$RC" = "0" ]; then
    echo "FAIL: add with no args should fail"; FAIL=$((FAIL+1))
else
    echo "ok: add with no args fails ($RC)"
fi

# 22. empty update is rejected
OUT="$($PY update 5 2>&1)"; RC=$?
assert_rc "update: empty => rc 2" 2 $RC

# 23. find with empty query
OUT="$($PY find '' 2>&1)"; RC=$?
assert_rc "find: empty query => rc 2" 2 $RC

# 24. unknown command
OUT="$($PY frobnicate 2>&1)"; RC=$?
if [ "$RC" = "0" ]; then
    echo "FAIL: unknown command should fail"; FAIL=$((FAIL+1))
else
    echo "ok: unknown command fails ($RC)"
fi

echo
if [ "$FAIL" = "0" ]; then
    echo "ALL VERIFICATION CHECKS PASSED"
    rm -rf "$WORK"
    exit 0
else
    echo "$FAIL CHECK(S) FAILED"
    echo "(work dir preserved at $WORK)"
    exit 1
fi
