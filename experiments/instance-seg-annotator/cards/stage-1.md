# Stage 1 — the request

Build a small tool I can run on my own machine.

I need to **annotate images for instance segmentation**. Concretely:

- I have a folder of images. I want to open the tool in my browser, see an image, and **draw shapes around
  individual objects** in it — one shape per object.
- Each object I draw gets a **class label** (e.g. "car", "tree", "building") from a list I can configure.
- There can be **several objects of several classes** in one image.
- I can **save** my work, and when I come back to that image later, my shapes are still there.
- I step through the folder image by image.
- It should **run from a container** (I'll `docker compose up` or similar) — I don't want to install a
  stack by hand.

Build it well. Use whatever technical approach you think is sensible. If something about the product is
genuinely ambiguous and the answer would change what you build, ask me one question at a time and I'll
answer as the product owner.

When you believe it does the above, say so and how to run it.
</content>
