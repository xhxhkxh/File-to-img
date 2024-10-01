# File-to-img
## Yes, these program could turn any file intoo an image.

When receiving a file, encoder would do this:
* create a file head, which includes the name of the file, and it's size. (This part is 500b in size, so don't make your filename too big.)
* Read binary data from the file, then convert them into the number.
* Write the numbers into the pixel, grouped three by three (suit for the RGB format).
* Save the image in current direction.

And the decoder do the reverse.

Here's an example image of the program:


