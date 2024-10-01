# File-to-img
## Yes, these program could turn any file intoo an image.

When receiving a file, encoder would do this:
* create a file head, which includes the name of the file, and it's size. (This part is 500b in size, so don't make your filename too big.)
* Read binary data from the file, then convert them into the number.
* Write the numbers into the pixel, grouped three by three (suit for the RGB format).
* Save the image in current direction.

And the decoder do the reverse.

## To decode the image, you need to place the image in the same dictionary with the decoder and rename the image as "res.png"

Here's an example image of the program: 
![Example image](https://github.com/xhxhkxh/File-to-img/blob/main/example/res.png?raw=true) <br>
The example image <br>
In the example image, you could see the colorful strips in the lest, it's the head of the file. <br>
And the black area in the middel, it's the reserved space for our 500b head section. <br>
The biggese colorful area is the size of the image, is the original data of the encoded file. <br>
the last black area is the reserved space for ... nothing. <br>

