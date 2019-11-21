from __future__ import print_function
import os
from datetime import datetime
import json
from time import sleep
from picamera import PiCamera
import argparse
import requests
import logging

import image_metrics

logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='system.log',
                    filemode='w')


def read_config(field):
    with open('config.json', 'r') as f:
        entry = json.load(f)[field]
    return entry


openweathermap_current = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&APPID=".format(
    read_config('sensor_location_city'))


def get_date(log=False):
    if log:
        date = datetime.today().strftime('%d.%m.%Y')
    else:
        date = datetime.today().strftime('%Y%m%d')
    return date


def get_time(log=False):
    if log:
        time = datetime.now().strftime('%H:%M:%S')
    else:
        time = datetime.now().strftime('%H%M%S')
    return time


class Image:
    def __init__(self, shutter_speed, iso):
        self.resolution = (1920, 1080)
        self.shutter_speed = shutter_speed
        self.iso = iso
        self.awb_mode = 'auto' # white balance - off, auto, sunlight, cloudy, shade, tungsten, fluorescent, incandescent, flash, horizon
        self.exposure_mode = 'auto'

        self.date = get_date(log=False)
        self.time = get_time(log=False)

        self.image_name = self.construct_file_name('image')
        self.metadata_name = self.construct_file_name('metadata')

        self.metadata = {
            'general': {
                'dateacquired': self.date,
                'timeacquired': self.time
            }
        }

        self.target_directory = os.path.join(os.getcwd(), 'data', self.date)

    def construct_file_name(self, file_type):
        # shutter speed and iso should not be in the final version
        file_name = '{}_{}_{}_{}_{}'.format(file_type, self.date, self.time, self.shutter_speed, self.iso)
        return file_name

    def validate_target_directory(self):
        """
        See if the target directory exists. If not - create it.
        :return:
        """
        if not os.path.isdir(self.target_directory):
            os.makedirs(self.target_directory)

            logging.info('created target directory: {}'.format(self.target_directory))

    def take_image(self):
        """
        take image
        :return: nothing
        """

        with PiCamera() as camera:
            # set all the camera parameters
            camera.resolution = self.resolution
            camera.shutter_speed = self.shutter_speed  # = exposure_time(?)
            camera.iso = self.iso
            camera.awb_mode = self.awb_mode
            camera.exposure_mode = self.exposure_mode

            sleep(1)

            camera.capture('{}/{}.jpg'.format(self.target_directory, self.image_name))
            self.get_camera_data()
            logging.info('captured image')

    # def get_exif_data(self):
    #     exif_data = {
    #        'exposure_time': self.camera.exif_tags['EXIF']['EXIF_ExposureTime']
    #        'focal_length': self.camera.exif_tags['EXIF']['EXIF_FocalLength']
    #        'shutter_speed': self.camera.exif_tags['EXIF']['EXIF_ShutterSpeedValue']
    #     }
    #
    #     self.metadata['exif_data'] = exif_data

    def get_camera_data(self):
        camera_data = {
            'width_px': self.resolution[0],
            'height_px': self.resolution[1],
            'exposure_ms': self.shutter_speed,
            'iso': self.iso,
            'awb': self.awb_mode,
            'image_name': self.image_name
        }

        self.metadata['image'] = camera_data

    def get_external_weather_data(self):
        """
        send request to openweathermap to get current weather data
        :return: nothing
        """
        url = openweathermap_current + read_config('OWM_API_KEY')
        r = requests.get(url)
        result_data = r.json()

        if r.status_code == 200:
            weather_data = {
                'desc': result_data['weather'][0].get('main', '?'),
                'pressure': result_data['main'].get('pressure', '?'),
                'humidity': result_data['main'].get('humidity', '?')
            }
            temperature_data = {
                'temp': result_data['main'].get('temp', '?'),
                'temp_min': result_data['main'].get('temp_min', '?'),
                'temp_max': result_data['main'].get('temp_max', '?')
            }
            wind_data = {
                'speed_kmh': result_data['wind'].get('speed', '?'),
                'direction_deg': result_data['wind'].get('deg', '?')
            }
            cloud_data = {
                'cloudiness_pct': result_data['clouds'].get('all', '?')
            }

            self.metadata['external_data'] = {
                'weather': weather_data,
                'wind': wind_data,
                'clouds': cloud_data,
                'temperature': temperature_data
            }

            logging.info('sucessfully requested external weather data')

        else:
            self.metadata['external_data'] = None

            logging.info('could not get external weather data, status code: {}'.format(r.status_code))

    def calculate_image_metrics(self):
        brightness = image_metrics.calculate_brightness(os.path.join(self.target_directory, self.image_name + '.jpg'),
                                                        file=True)
        self.metadata['image']['brightness'] = brightness

    def write_metadata(self):
        with open('{}/{}.json'.format(self.target_directory, self.metadata_name), 'w') as metadata:
            json.dump(self.metadata, metadata)

    def do_everything(self):
        # almost sure that this is not the best way to do this
        self.validate_target_directory()
        self.take_image()
        self.get_external_weather_data()
        self.calculate_image_metrics()
        self.write_metadata()


def argument_parser():
    aparser = argparse.ArgumentParser(description='Take all the images!')
    aparser.add_argument('--exposure', '-e', type=int, help='Exposure time in ms.')
    aparser.add_argument('--iso', '-i', type=int, help='ISO')
    aparser.add_argument('--delay', '--d', type=int, help='Acquisition delay in ms.', required=False)
    aparser.add_argument('--mode', choices=['single', 'continuous'], help='Single picture or continuous capture.')
    arguments = aparser.parse_args()

    return arguments


def main():
    arguments = argument_parser()
    expo = arguments.exposure
    iso = arguments.iso
    acquisition_delay = arguments.delay
    mode = arguments.mode

    if not acquisition_delay:
        acquisition_delay = read_config('acquisition_delay')

    # exposures = [200, 400, 800, 1000, 1200, 1400]
    exposures = [expo for expo in range(100, 2100, 100)]

    if mode == 'continuous':
        try:
            while True:
                for exposure in exposures:
                    image = Image(exposure, iso)
                    image.do_everything()

                sleep(acquisition_delay)
        except KeyboardInterrupt:
            print('Manual break by user')
        except Exception as e:
            print('{} went wrong ... stopping!'.format(e))
    else:
        image = Image(expo, iso)
        image.do_everything()


if __name__ == '__main__':
    main()
