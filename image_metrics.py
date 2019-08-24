from PIL import Image
import sys


def calculate_brightness(image, file=False):
    if file:
        image = Image.open(image)
    else:
        image = Image.fromarray(image)

    greyscale_image = image.convert('L')
    histogram = greyscale_image.histogram()
    pixels = sum(histogram)
    brightness = scale = len(histogram)

    for index in range(0, scale):
        ratio = histogram[index] / pixels
        brightness += ratio * (-scale + index)

    return 1 if brightness == 255 else brightness / scale


def main():
    image = sys.argv[1]
    print(calculate_brightness(image, file=True))


if __name__ == '__main__':
    main()



