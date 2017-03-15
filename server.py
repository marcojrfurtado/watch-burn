#!/usr/bin/env python
"""Watch the World burn! Web App."""

import os

import config
import ee
import jinja2
import webapp2
from datetime import date, timedelta
import traceback
from google.appengine.api import urlfetch


# Extend  request deadline
urlfetch.set_default_fetch_deadline(60)



from cache import Cache

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class MainPage(webapp2.RequestHandler):

    @staticmethod
    def _date_str(d):
        date_format = '%Y-%m-%d'
        return d.strftime(date_format)

    @staticmethod
    def _confidence_function(image):
        highValue = image.select(['confidence']).gt(50)
        return highValue.updateMask(highValue)


    def process(self,date_range_start,date_range_end,topFireSpots=10):


        ee.Initialize(config.EE_CREDENTIALS)

        # Get image collections
        firms = ee.ImageCollection('FIRMS')


        firms2017 = firms.filterDate(self._date_str(date_range_start), self._date_str(date_range_end))

        # Mask based on confidence value
        confidentFirms2017 = firms2017.map(self._confidence_function)

        # Create image with the confident count
        dotImage = confidentFirms2017.count()

        # Get list of World countries
        countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')

        # Get fire by country
        fireByCountries = dotImage.reduceRegions(collection=countries, reducer=ee.Reducer.count(), scale=3000)

        # filter all those that had at least one event
        fireByCountries = fireByCountries.filterMetadata("count", "greater_than", 0)

        # Get the max count
        fireMax = fireByCountries.aggregate_max('count')

        # Create an empty image into which to paint the features, cast to RGB length.
        redMap = ee.Image().uint32()

        # Add a colored layer based on the count
        redMap = redMap.paint(featureCollection=fireByCountries, color='count')

        redMapVisualization = redMap.visualize(min=1,max=fireMax,opacity=0.7,palette=['FFEDED','FF0000'])

        fireSpotsVisualization = dotImage.visualize(palette=['black'],forceRgbOutput=True)

        # Create a mosaic to merge fire spots and country measures
        mapCollection = ee.ImageCollection([redMapVisualization,fireSpotsVisualization])
        mosaic = mapCollection.mosaic()

        # Get the list of top countries
        topCountries = fireByCountries.sort("count", False).toList(topFireSpots)
        topCountries = topCountries.getInfo()
        topCountriesProperties = [ country['properties'] for country in topCountries ]


        # Cache information about map
        return mosaic.getMapId(), topCountriesProperties



    def get(self):

        # Get information for a specific date range
        date_range_start = date.today() - timedelta(days=2)
        date_range_end = date.today() - timedelta(days=1)

        mapid, top10 = Cache.instance().get_vals()
        if mapid is None:
            try:
                mapid, top10 = self.process(date_range_start,date_range_end)
            except:
                traceback.print_exc()
                error_page = jinja_environment.get_template('500.html')
                self.response.out.write(error_page.render())
                return

            Cache.instance().set_vals(mapid, top10)

        # These could be put directly into template.render, but it
        # helps make the script more readable to pull them out here, especially
        # if this is expanded to include more variables.
        template_values = {
            'mapid': mapid['mapid'],
            'token': mapid['token'],
            'countries': top10,
            'range_start' : self._date_str(date_range_start),
            'range_end': self._date_str(date_range_end)
        }
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
