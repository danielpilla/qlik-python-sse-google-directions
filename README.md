# Python Google Directions & Waypoint Optimization SSE for Qlik

![Waypoint Optimization](https://s3.amazonaws.com/dpi-sse/qlik-python-sse-google-directions/wayptoint-optimization-sheet-1.png)

## REQUIREMENTS

- **Assuming prerequisite: [Python with Qlik Sense AAI – Environment Setup](https://s3.amazonaws.com/dpi-sse/DPI+-+Qlik+Sense+AAI+and+Python+Environment+Setup.pdf)**
	- This is not mandatory and is intended for those who are not as familiar with Python to setup a virtual environment. Feel free to follow the below instructions flexibly if you have experience.
- **Waypoint Optimization example demo app also leverages the [Geocoding SSE](https://github.com/danielpilla/qlik-python-sse-geocoding) to first place a pin on a map as the starting point. To have app work properly, this SSE needs to be configured as well.**
- Qlik Sense June 2017+
- QlikView November 2017+
    - *This guide is designed for Qlik Sense but may be used with QlikView. See how to setup Analytic Connections within QlikView [here](https://help.qlik.com/en-US/qlikview/November2017/Subsystems/Client/Content/Analytic_connections.htm)*
- Python 3.5.3 64 bit *(3.4+ but tested on 3.5.3)*
- Python Libraries: grpcio, googlemaps, polyline
- Qlik GeoAnalytics to visualize routes and geocoding in demo apps

## LAYOUT

- [Prepare your Project Directory](#prepare-your-project-directory)
- [Install Python Libraries and Required Software](#install-python-libraries-and-required-software)
- [Setup an AAI Connection in the QMC](#setup-an-aai-connection-in-the-qmc)
- [Copy the Package Contents and Import Examples](#copy-the-package-contents-and-import-examples)
- [Prepare And Start Services](#prepare-and-start-services)
- [Leverage the Google Directions API from within Qlik Sense](#leverage-the-google-directions-api-from-within-qlik-sense)

 
## PREPARE YOUR PROJECT DIRECTORY
>### <span style="color:red">ALERT</span>
><span style="color:red">
>Virtual environments are not necessary, but are frequently considered a best practice when handling multiple Python projects.
></span>

1. Open a command prompt
2. Make a new project folder called QlikSenseAAI, where all of our projects will live that leverage the QlikSenseAAI virtual environment that we’ve created. Let’s place it under ‘C:\Users\{Your Username}’. If you have already created this folder in another guide, simply skip this step.

3. We now want to leverage our virtual environment. If you are not already in your environment, enter it by executing:

```shell
$ workon QlikSenseAAI
```

4. Now, ensuring you are in the ‘QlikSenseAAI’ folder that you created (if you have followed another guide, it might redirect you to a prior working directory if you've set a default, execute the following commands to create and navigate into your project’s folder structure:
```
$ cd QlikSenseAAI
$ mkdir Directions
$ cd Directions
```


5. Optionally, you can bind the current working directory as the virtual environment’s default. Execute (Note the period!):
```shell
$ setprojectdir .
```
6. We have now set the stage for our environment. To navigate back into this project in the future, simply execute:
```shell
$ workon QlikSenseAAI
```

This will take you back into the environment with the default directory that we set above. To change the
directory for future projects within the same environment, change your directory to the desired path and reset
the working directory with ‘setprojectdir .’


## INSTALL PYTHON LIBRARIES AND REQUIRED SOFTWARE

1. Open a command prompt or continue in your current command prompt, ensuring that you are currently within the virtual environment—you will see (QlikSenseAAI) preceding the directory if so. If you are not, execute:
```shell
$ workon QlikSenseAAI
```
2. Execute the following commands. If you have followed a previous guide, you have more than likely already installed grpcio):

```shell
$ pip install grpcio
$ pip install googlemaps
$ pip install polyline
```

## SET UP AN AAI CONNECTION IN THE QMC

1. Navigate to the QMC and select ‘Analytic connections’
2. Fill in the **Name**, **Host**, and **Port** parameters -- these are mandatory.
    - **Name** is the alias for the analytic connection. For the example qvf to work without modifications, name it 'PythonDirections'
    - **Host** is the location of where the service is running. If you installed this locally, you can use 'localhost'
    - **Port** is the target port in which the service is running. This module is setup to run on 50056, however that can be easily modified by searching for ‘-port’ in the ‘ExtensionService_directions.py’ file and changing the ‘default’ parameter to an available port.
3. Click ‘Apply’, and you’ve now created a new analytics connection.


## COPY THE PACKAGE CONTENTS AND IMPORT EXAMPLES

1. Now we want to setup our directions service and app. Let’s start by copying over the contents of the example
    from this package to the ‘..\QlikSenseAAI\Directions\’ location. Alternatively you can simply clone the repository.
2. After copying over the contents, go ahead and import the example qvfs found [here](https://s3.amazonaws.com/dpi-sse/qlik-python-sse-google-directions/DPI+-+Google+Directions.qvf) and [here](https://s3.amazonaws.com/dpi-sse/qlik-python-sse-google-directions/DPI+-+Python+Google+Waypoint+Optimization.qvf).
3. Lastly, import the *qsvariable* extension found [here](https://github.com/erikwett/qsVariable) and the *Simple Table with Image & Link Detectio*n found [here](https://github.com/danielpilla/sense-images-links-extension).


## PREPARE AND START SERVICES

1. At this point the setup is complete, and we now need to start the directions extension service. To do so, navigate back to the command prompt. Please make sure that you are inside of the virtual environment.
2. Once at the command prompt and within your environment, execute (note two underscores on each side):
```shell
$ python ExtensionService_directions.py
```
3. We now need to restart the Qlik Sense engine service so that it can register the new SSE service. To do so,
    navigate to windows Services and restart the ‘Qlik Sense Engine Service’
4. You should now see in the command prompt that the Qlik Sense Engine has registered the functions *GoogleDirections()* and *WaypointOptimization()* from the extension service over port 50056, or whichever port you’ve chosen to leverage.


## LEVERAGE THE GOOGLE DIRECTIONS API FROM WITHIN SENSE

First and foremost, you will need to link a Google account to receive a [Google Directions API key](https://developers.google.com/maps/documentation/directions/get-api-key). Once you have this key, open up *ExtensionService_directions.py* and add your key where you see: 

```gmaps = googlemaps.Client(key=’YourKeyHere’)```

*Once you've entered your new key you will need to make sure you restart both the SSE service and the Qlik Sense Engine.*

### Google Directions

1. The *GoogleDirections()* function leverages the [googlemaps Python package](https://github.com/googlemaps/google-maps-services-python) as well as the [polyline package](https://github.com/hicsail/polyline), and the function I’ve written accepts five mandatory arguments: 
    - *Start Location (string)*: can be an address, city, state, named location, etc
    - *End Location (string)*: can be an address, city, state, named location, etc
    - *Mode (string)*: see [Google Travel Modes](https://developers.google.com/maps/documentation/directions/intro#TravelModes)
    - *The data to be returned (string)*: this can be one of 5 different options
    	- *all* -  this will return every result in a single list so that you can parse within Qlik to save calls
    	- *coordinates* - this returns the list of all coordinates, and works as a line object dimension with GeoAnalytics. This is the coordinate route. 
    	- *instructions* - this returns the list of step by step driving instructions
    	- *duration* - this returns the total duration in minutes 
    	- *distance* - this returns the total distance in miles
    - *Alternative (string)* - this is a string Boolean represented as 'true' or 'false' to return the first alternate route
    	
2. Example function calls:
	
    *Returns the total duration of the trip*:
    ``` PythonDirections.GoogleDirections('$(vStart)','$(vEnd)','driving','duration','false') ``` 
    
    *Returns the total distance of the trip of the first alternate route*:
    ``` PythonDirections.GoogleDirections('$(vStart)','$(vEnd)',’driving’,distance,’true’)  ```
    
I have created an application that demonstrates three different methods of implementation, but there are certainly many other scenarios and use cases.
- Sheet 1: Routing from input box to input box locations

![Sheet 1](https://s3.amazonaws.com/dpi-sse/qlik-python-sse-google-directions/directions-sheet-1.png)

- Sheet 2: Routing from selecting two address values within a filter pane or on the map

![Sheet 2](https://s3.amazonaws.com/dpi-sse/qlik-python-sse-google-directions/directions-sheet-2.png)

- Sheet 3: Routing from an input box location to a selection in a field or on the map

![Sheet 3](https://s3.amazonaws.com/dpi-sse/qlik-python-sse-google-directions/directions-sheet-3.png)
       
### Waypoint Optimization (Traveling Salesman)

1. The WaypointOptimization() leverages the [googlemaps Python package](https://github.com/googlemaps/google-maps-services-python) as well as the [polyline package](https://github.com/hicsail/polyline), and the function I’ve written accepts five mandatory arguments: 
	- *Start Location (string)*: can be an address, city, state, named location, etc
	- *End Location (string)*: can be an address, city, state, named location, etc
	- *Mode (string)*: see [Google Travel Modes](https://developers.google.com/maps/documentation/directions/intro#TravelModes)
	- *The data to be returned (string)*: this can be 3 different options:
		- *all* - returns routes, ordered points, and ordered location names so it can be parsed on the front-end. The above returns are sent in a single triple pipe delimited (|||) string for parsing.
		- *route* - can be used for a GeoAnalytics Line Map dimension
		- *points* - returns a string of ordered points
	- *Waypoints (string)*: a list of up to 10 waypoints (the API goes up to 23 but my example app allows for 10), each delimited with a pipe (|).

2. Example function calls:
	
    *Returns all data from the optimized route including two waypoints of Albany and Austin*:
    ``` PythonDirections.WaypointOptimization(‘$(vStart)’,’$(vEnd)’,’driving’,’all’,’Albany, NY|Austin, TX|’)  ``` 
    
    *Returns the optimized route to be used in a GeoAnalytics Line Layer between two points with waypoints in Denver and Newport*:
    ``` PythonDirections.WaypointOptimization(‘$(vStart)’,’$(vEnd)’,’bicycling’,’route’,’Denver, CO|Newport, RI|’)   ```
    
3. Example application:
	- The example I’ve provided allows up to 10 waypoints (Google supports up to 23, you could easily adjust the app to allow more). You enter a location into the input box on the top left, and that location is used as your start and end. You then select a transportation mode (driving is the default) followed by up to 10 waypoints. If you have a location entered and waypoints>=2 and waypoints<=10, the map will render the route as well as the ordered points in the order in which to most optimally traverse. 

![Waypoint Optimization](https://s3.amazonaws.com/dpi-sse/qlik-python-sse-google-directions/wayptoint-optimization-sheet-1.png)