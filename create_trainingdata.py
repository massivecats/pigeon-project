import cv2
import numpy as np
import argparse
import os


def argument_parser():
    aparser = argparse.ArgumentParser(description='Take all the images!')
    aparser.add_argument('--size', '-s', type=int, help='Chip size in px.')
    aparser.add_argument('--mode', '-m', choices=['single', 'multiple'], help='Single image or multiple images.')
    aparser.add_argument('--input', '-i', required=False, help='Input image or input directory.')
    arguments = aparser.parse_args()

    return arguments


def save_chips(image, chip_coordinates, name):
    for num, coord in enumerate(chip_coordinates):
        x = coord[0]
        y = coord[1]
        # print(x, y)
        # print(x - 50, x + 50, y - 50, y + 50)

        # if the coordinates of the chip are outside of the image, the chip will not be saved
        my_chip = image[x - 50:x + 50,
                        y - 50:y + 50]

        cv2.imwrite(os.path.join(os.getcwd(), f'chip_{num}_{name}.jpg'), my_chip)


def image_previewer(data_input, window_name):
    # the image that is displayed, the drawn rectangles are created directly on this image, thus you can not extract
    # the chips from this image and have to create a copy
    img = cv2.imread(data_input)

    # a copy of the original image where the chips are extracted from
    cut_img = img.copy()

    size = 100  # size in px of the rectangles and final chips
    chips = []

    def draw_rectangle(event, x, y, flags, param):
        pt1 = (int(x - size / 2), int(y - size / 2))
        pt2 = (int(x + size / 2), int(y + size / 2))

        if event == cv2.EVENT_LBUTTONDOWN:
            chips.append((y, x))
            cv2.rectangle(img, pt1=pt1, pt2=pt2, color=(255, 0, 0), thickness=2)

    cv2.namedWindow(winname=window_name)
    cv2.setMouseCallback(window_name, draw_rectangle)

    while True:
        cv2.imshow(window_name, img)

        # if waited for 20ms AND press of esc, don't save the chips of this image
        if cv2.waitKey(20) & 0xFF == 27:
            break

        # if waited for 20ms AND press of enter, save chips from the drawn rectangles
        if cv2.waitKey(20) & 0xFF == 13:
            save_chips(cut_img, chips, window_name)
            break

    cv2.destroyAllWindows()


def main():
    arguments = argument_parser()
    size = arguments.size
    mode = arguments.mode
    data_input = arguments.input

    if mode == 'single':
        filename = data_input.split('\\')[-1]
        img_name = filename.split('.')[0]
        image_previewer(data_input, img_name)
    else:
        for root, dirs, files in os.walk(data_input):
            print(root.split('\\')[-2])
            for file in files:
                if file.endswith('.jpg'):
                    print(os.path.join(root, file))

                    name = file.split('.')[0]

                    image_previewer(os.path.join(root, file), name)


if __name__ == '__main__':
    main()
