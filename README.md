###Landsat8NDVI

This application computes the average "Normalized Difference Vegetation Index" (NDVI) for a given
Region of Interest based of available Landsat8 satellite data.  NDVI is a remote sensing index that uses the relative differences
in the reflectance properties of the Near-Infrared wavelength of light and the Red (visible) wavelength of light
(information that is captured by many satellite sensors) to estimate the amount of "greeness" of a given surface.
This index is highly correletated with green vegetative biomass, gross primary productivity, and other ecological
measures, and is used often within the remote sensing literature.

This application uses the Google Maps Javascript API, allowing users to specify a polygon for their
region of interest on a Google Map.  The coordinates of a polygon are specified in the API in an
"MVC Array" object.  Upon completion of the polygon drawing event, the MVC Array for the specified polygon
is queried in javascript from the html form, these coordinates are reconfigured to a "standard" javascript array,
the array is then "stringified" to allow this information to be sent to the server.  The use is then asked
to click a hyperlink button to actually submit this information.  Upon clicking the hyperlink,
the information is sent to the server using Ajax, and a "success" alert is fired to alert the user the polygon has
been submitted.  These polygon coordinates are upacked in a "./reciever" endroute in the python controller,
stored in a local variable called "polygon_data" and then passed to the "/formsubmit" endroute using a flask session.
(This trick prevents the need to implement a database for storage of a single variable).  Here, in
the polygon data will be processed (described later).

Back to the initial form document... the user is also asked to input a calendar date, and then hit a "submit"
button.  When that button is clicked, two javascript "checks" are triggered via Ajax.  The first calls the
"/reciever" endpoint (this time using a "Get" request; the hyperlink "Add Region of Interest" above the
"submit" button uses a "Post" request), to ensure that a Polygon was indeed drawn and submitted by the user.  The
second calls a "/check" endpoint to verify that a date was submitted.  Javascript alerts are issued to the user if any information
has been neglected.  If these checkpoints are passed, the form button calls the "/formsubmit" endpoint.  Here, one last
check is performed before data processing: The polygon coordinates are unpacked from the session cookie, and the size
of the polygon is checked to make sure it is small enough for processing.  An "oops" page appears if the polygon is too
big, asking the user to return to the form and try again.

Data is processed using the Google Earth Engine python API.  To authenticate the app to Google Earth Engine,
I requested permission from Google for a Google Earth Engine "Service Account".  After recieving permission,
I downloaded the necessery credentials, and initialized Google Earth Engine. 

Data processing asks Google Earth Engine to retrieve Landsat8 satellite imagery for the first date following the user-
inputted date, mask the image for clouds, clip it to the bounds of the user-specified geometry, and calculate NDVI.
Finally, the NDVI value and the date for the image on which NDVI is based are returned to the client using Jinja.

An accompanying CSS file was created to stylize my app.

I am currently troubleshooting deployment of the app to the Google cloud server.
