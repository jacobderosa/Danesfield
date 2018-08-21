#!/usr/bin/env python

from __future__ import print_function

import sys
import os
import argparse
import logging
import numpy
import gdal
import pyproj

from danesfield import gdal_utils
from orthorectify_list import intersection


def main(args):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="Rank images by most area overlap, least cloud \
                                     cover, and most nadir with respect to a DSM")
    parser.add_argument(
        '--dsm', required=True,
        help='File path to DSM')
    parser.add_argument(
        'image_files', nargs='+')

    args = parser.parse_args(args)

    # Method taken from the 'orthorectify_list.py' script
    angles = numpy.zeros(len(args.image_files))
    cloudCover = numpy.zeros(len(args.image_files))
    bounds = numpy.zeros([len(args.image_files), 4])

    outProj = pyproj.Proj('+proj=longlat +datum=WGS84')
    dsmImage = gdal.Open(args.dsm, gdal.GA_ReadOnly)
    dsmBounds = gdal_utils.gdal_bounding_box(dsmImage, outProj)
    dsmArea = (dsmBounds[2] - dsmBounds[0]) * (dsmBounds[3] - dsmBounds[1])

    areas = numpy.zeros(len(args.image_files))

    for i, image_file in enumerate(args.image_files):
        sourceImage = gdal.Open(image_file, gdal.GA_ReadOnly)
        metaData = sourceImage.GetMetadata()
        angles[i] = metaData['NITF_CSEXRA_OBLIQUITY_ANGLE']
        cloudCover[i] = metaData['NITF_PIAIMC_CLOUDCVR']
        bounds = gdal_utils.gdal_bounding_box(sourceImage, outProj)

        imageIntersectDsm = intersection(dsmBounds, bounds)
        areaImageIntersectDsm = (imageIntersectDsm[2] - imageIntersectDsm[0]) *\
            (imageIntersectDsm[3] - imageIntersectDsm[1]) if imageIntersectDsm else 0
        # area of DSM not covered
        areas[i] = dsmArea - areaImageIntersectDsm

    sortIndex = numpy.lexsort((angles, cloudCover, areas))

    return numpy.asarray(args.image_files)[sortIndex]


if __name__ == '__main__':
    loglevel = os.environ.get('LOGLEVEL', 'INFO').upper()
    logging.basicConfig(level=loglevel)

    try:
        print("\n".join(main(sys.argv[1:])))
    except Exception as e:
        logging.exception(e)
        sys.exit(1)