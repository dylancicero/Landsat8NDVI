#!flask/bin/python

import sys
import flask
import time
from flask import Flask, render_template, request, redirect, Response, session, jsonify
import random, json
import requests
import six
import ee
import googleapiclient
from google.appengine.api import urlfetch
import datetime
import math
import os

app = Flask(__name__)
app.secret_key = 'key'



@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/check', methods=['GET'])
def check():
    date = request.args.get("date")

    if date:
        return jsonify(True)
    else:
        return jsonify(False)

trial = ""
@app.route('/reciever', methods=['GET','POST'])
def reciever():
    polygon_data = []
    if request.method == "POST":
        polygon_data = request.get_json(force = True)

        # Use Flask session to send polygon_data from this endpoint into
        # the '/formsubmit' endpoint where it will be processed
        # (This is more efficient than creating a database for the sake of
        # this one variable alone)
        session['polygon'] = polygon_data
        empty = ""
        return empty

    # Ensure that polygon was submitted
    else:
        polygon_data = session.get('polygon', None)
        if polygon_data == None:
            return jsonify(False)
        else:
            return jsonify(True)


@app.route('/formsubmit', methods=['POST'])
def submitted_form():
    # Accept date from form
    date = request.form['doi']

    # Accept polygon_data from session
    polygon_data = session.get('polygon', None)
    session.clear()

    # Process polygon data coordinates from json dictionary to appropriate
    # form as input to the Google Earth Engine Geometry.Polygon object
    list1 = []
    for item in polygon_data:
        list2 = []
        for k,v in item.iteritems():
            list2.append(v)
        list1.append(list2)

    # Initialie Google Earth Engine using ServiceAccountCredentials
    EE_ACCOUNT = 'sentinelatmosphericcorrection@sentinelatmosphericcorrection.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(EE_ACCOUNT, 'privatekey.json')
    ee.Initialize(credentials)

    # pass user defined geomtry coordinates into Earth Engine Geometry.Polygon object
    geometry = ee.Geometry.Polygon([list1]);
    area = geometry.area().getInfo()/1000000

    if area > 10:
        return render_template('oops.html', area = area)

    # pass user defined dates into Earth Engine date range object
    date = ee.Date(date)
    date1 = date.advance(1000, 'day')

    # Retrieve Landsat 8 imagery and filter by dates and location
    Landsat8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")
    Landsat8Bounded = Landsat8.filterBounds(geometry).filterDate(date, date1)

    # Clip the resultant imagery to specific geometry
    def clip(image):
        return image.clip(geometry)

    # Map function to all images in collection
    landsat8Clipped = Landsat8Bounded.map(clip)

    # Mask out all cloudy or defective pixels from the image collection
    # (Source: The below script comes directly from "Cloud Masking: Landsat 8
    # Surface Reflectance" on the GEE Scripts tab.  It is not original work)
    # 1) Develop function to calculate NSVI from a landsat 8 image
    def maskL8sr(image):
        # Bits 3 and 5 are cloud shadow and cloud, respectively
        cloudShadowBitMask = 1 << 3
        cloudsBitMask = 1 << 5
        # Get the pixel QA band
        qa = image.select('pixel_qa')
        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0) and (qa.bitwiseAnd(cloudsBitMask).eq(0))
        # Return the masked image, scaled to TOA reflectance, without the QA bands.
        return image.updateMask(mask).copyProperties(image, ["system:time_start"])
    # 2) Map function over image collection
    landsat8ClippedMasked = landsat8Clipped.map(maskL8sr)

    # Calculate the Normalized Difference Vegetation index
    # 1) Develop function to calculate NDVI from a landsat 8 image
    def NDVI(image):
        ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
        return image.addBands(ndvi)

    # 2.) Map function over image collection
    L8CollectionNDVI = landsat8ClippedMasked.map(NDVI);

    # Obtain date and NDVI from first image in collection and
    # transport to "submitted_form.html" via jinja
    date3 = ee.Image(Landsat8Bounded.first()).date()
    getDate = ee.Image(date3).getInfo()
    output2 = time.strftime('%m/%d/%Y', time.gmtime(float(getDate.values()[1] * 1.0) / 1000))
    print(output2)
    time.sleep(1)

    ndviImageMean = L8CollectionNDVI.first().reduceRegion(ee.Reducer.mean(),geometry,30)
    output = ndviImageMean.getInfo()['NDVI']
    print(output)
    time.sleep(1)

    return render_template('submitted_form.html', output = output, output2 = output2)
