#! /usr/bin/env python3
import argparse
import json
import logging
import logging.config
import os
import sys
import time
from concurrent import futures
from datetime import datetime

import googlemaps
import polyline

import ServerSideExtension_pb2 as SSE
import grpc
from SSEData_directions import FunctionType, \
                               get_func_type
from ScriptEval_directions import ScriptEval

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

## add your Google Directions API Key here
gmaps = googlemaps.Client(key='ENTER YOUR API KEY HERE')


class ExtensionService(SSE.ConnectorServicer):
    """
    A simple SSE-plugin created for the HelloWorld example.
    """

    def __init__(self, funcdef_file):
        """
        Class initializer.
        :param funcdef_file: a function definition JSON file
        """
        self._function_definitions = funcdef_file
        self.scriptEval = ScriptEval()
        if not os.path.exists('logs'):
            os.mkdir('logs')
        logging.config.fileConfig('logger.config')
        logging.info('Logging enabled')

    @property
    def function_definitions(self):
        """
        :return: json file with function definitions
        """
        return self._function_definitions

    @property
    def functions(self):
        """
        :return: Mapping of function id and implementation
        """
        return {
            0: '_directions',
            1: '_waypointOptimization'
        }

    @staticmethod
    def _get_function_id(context):
        """
        Retrieve function id from header.
        :param context: context
        :return: function id
        """
        metadata = dict(context.invocation_metadata())
        header = SSE.FunctionRequestHeader()
        header.ParseFromString(metadata['qlik-functionrequestheader-bin'])

        return header.functionId

    """
    Implementation of added functions.
    """


    @staticmethod
    def _directions(request, context):
        global gmaps

        # grab the time to be used in the directions
        now = datetime.now()
        
        # Iterate over bundled rows
        for request_rows in request:
            
            # Iterate over rows
            for row in request_rows.rows:
                        
                # The first strData is the starting point
                start = [d.strData for d in row.duals][0]

                # The second strData is the ending point
                end = [d.strData for d in row.duals][1]

                # The third strData is the transportation mode
                mode = [d.strData for d in row.duals][2]

                # The fourth strData is return response that you would like
                # these can be:
                #   'all' - this will return every result in a single list so that you can parse within Qlik and save API calls
                #   'coordinates' - can be used for a GeoAnalytics Line Map
                #   'instructions' - these are step by step instructions
                #   'durations' - these are each of the durations
                #   'distances' - these are each of the distances
                #   'duration' - this is the total duration in minutes
                #   'distance' - this is the total distance in miles
                response = [d.strData for d in row.duals][3]


                # The fifth strData is whether you would like the alternative route instead
                alternative = str([d.strData for d in row.duals][4]).lower()
                if alternative != 'true' and alternative != 'false':
                    resultIndex = 0
                    alternativeFlag = False
                else:
                    if alternative == 'true':
                        resultIndex = 1
                        alternativeFlag = True
                    else:
                        resultIndex = 0
                        alternativeFlag = False

                # get directions
                stepsCoordList = []
                stepsInstructList = []
                durationList = []
                distanceList = []
                modeList = []
                startList = []
                endList = []
                instructionsPretty = []
                sumDurationList = []
                sumDistanceList = []
                

                result = gmaps.directions(start,
                                          end,
                                          mode=mode,
                                          departure_time=now,
                                          alternatives=alternativeFlag)

                directions_dictionary = result[resultIndex]
                steps = directions_dictionary['legs'][0]['steps']

                i=0
                for step in steps:
                    i+=1
                    # flipflop lat and long to change order for GeoAnalytics
                    tempCoordList = [list(elem) for elem in polyline.decode(step['polyline']['points'])]
                    flipflopped = [[elem[1],elem[0]] for elem in tempCoordList]
                    
                    stepsCoordList.append(flipflopped)

                    stepsInstructList.append('|' + str(i) + ': ' + str(step['html_instructions']))
                    
                    durationList.append(
                        ['Value: ' + str(step['duration']['value']),'Text: ' + str(step['duration']['text'])]
                        )
                    
                    sumDurationList.append(float(str(step['duration']['text']).split(' ')[0]))

                    distanceList.append(
                        ['Value: ' + str(step['distance']['value']),'Text: ' + str(step['distance']['text'])]
                        )

                    if 'ft' in str(step['distance']['text']):
                        sumDistanceList.append(float(str(step['distance']['text']).split(' ')[0])/5280)
                    elif 'mi' in str(step['distance']['text']):
                        sumDistanceList.append(float(str(step['distance']['text']).split(' ')[0]))
                        
                    modeList.append(step['travel_mode'])
                    
                    startList.append(
                        ['Lat: ' + str(step['start_location']['lat']),'Long: ' + str(step['start_location']['lng'])]
                        )
                    
                    endList.append(
                        ['Lat: ' + str(step['end_location']['lat']),'Long: ' + str(step['end_location']['lng'])]
                        )
                    
                    instructionsPretty.append(
                        '|' + str(i) + ': ' + str(step['html_instructions'])+ ', Distance: ' + str(step['distance']['text'])+ ', Duration: ' + str(step['duration']['text'])
                        )



        try:
            # wrap all directions into a single list
            if response=='coordinates':
                directionsResult = stepsCoordList
            elif response=='instructions':
                directionsResult = instructionsPretty
            elif response=='durations':
                directionsResult = durationList
            elif response=='distances':
                directionsResult = distanceList
            elif response=='duration':
                directionsResult = sum(sumDurationList)
            elif response=='distance':
                directionsResult = sum(sumDistanceList)
            else:
                directionsResult = [instructionsPretty,stepsCoordList]     
        except:
            pass

        directionsResult = [directionsResult]

        # Create an iterable of dual with the result
        duals = iter([[SSE.Dual(strData=str(c))] for c in directionsResult])

        # Yield the row data as bundled rows
        yield SSE.BundledRows(rows=[SSE.Row(duals=d) for d in duals])




    @staticmethod
    def _waypointOptimization(request, context):
        global gmaps

        # grab the time to be used in the directions
        now = datetime.now()
        
        # Iterate over bundled rows
        for request_rows in request:
            
            # Iterate over rows
            for row in request_rows.rows:        
                # The first strData is the starting point
                start = [d.strData for d in row.duals][0]

                # The second strData is the ending point
                end = [d.strData for d in row.duals][1]

                # The third strData is the transportation mode
                mode = [d.strData for d in row.duals][2]

                # The fourth strData is return response that you would like
                # these can be:
                #   'route' - can be used for a GeoAnalytics Line Map
                #   'points' - returns a string of ordered points
                #   'all' - returns routes, ordered points, and ordered location names so it can be parsed on the front to minimize calls
                response = [d.strData for d in row.duals][3]


                # The fifth strData is the waypoint locations delimited by a '|'
                waypointsTemp = str([d.strData for d in row.duals][4])
                waypointList = waypointsTemp.split('|')
                waypoints = 'optimize:true|' + waypointsTemp

                result = gmaps.directions(start,
                                          end,
                                          mode=mode,
                                          departure_time=now,
                                          waypoints=waypoints)

                waypointOrder = result[0]['waypoint_order']
                overviewPolylineTemp = [list(elem) for elem in polyline.decode(result[0]['overview_polyline']['points'])]
                overviewPolyline = [[elem[1],elem[0]] for elem in overviewPolylineTemp]

                orderedLocationList = [waypointList[i] for i in waypointOrder]

                orderedLocationString = '||'.join(str(i) for i in orderedLocationList)

                legs = result[0]['legs']

                pointList = []
                i = 0
                for leg in legs:
                    if i==0:
                        start = legs[i]['start_location']
                        startPoint = [start['lng'], start['lat']]
                        pointList.append(startPoint)
                        
                    pointTemp = legs[i]['end_location']
                    point = [pointTemp['lng'], pointTemp['lat']]
                    pointList.append(point)

                    i+=1

                pointString = '||'.join(str(i) for i in pointList)

        if response=='points':
            result = pointString
        elif response=='route':
            result = overviewPolyline
        else:
            result = pointString + '|||' + str(overviewPolyline) + '|||' + orderedLocationString

        result = [result]

        # Create an iterable of dual with the result
        duals = iter([[SSE.Dual(strData=str(c))] for c in result])

        # Yield the row data as bundled rows
        yield SSE.BundledRows(rows=[SSE.Row(duals=d) for d in duals])


    """
    Implementation of rpc functions.
    """

    def GetCapabilities(self, request, context):
        """
        Get capabilities.
        Note that either request or context is used in the implementation of this method, but still added as
        parameters. The reason is that gRPC always sends both when making a function call and therefore we must include
        them to avoid error messages regarding too many parameters provided from the client.
        :param request: the request, not used in this method.
        :param context: the context, not used in this method.
        :return: the capabilities.
        """
        logging.info('GetCapabilities')
        # Create an instance of the Capabilities grpc message
        # Enable(or disable) script evaluation
        # Set values for pluginIdentifier and pluginVersion
        capabilities = SSE.Capabilities(allowScript=True,
                                        pluginIdentifier='Hello World - Qlik',
                                        pluginVersion='v1.0.0-beta1')

        # If user defined functions supported, add the definitions to the message
        with open(self.function_definitions) as json_file:
            # Iterate over each function definition and add data to the capabilities grpc message
            for definition in json.load(json_file)['Functions']:
                function = capabilities.functions.add()
                function.name = definition['Name']
                function.functionId = definition['Id']
                function.functionType = definition['Type']
                function.returnType = definition['ReturnType']

                # Retrieve name and type of each parameter
                for param_name, param_type in sorted(definition['Params'].items()):
                    function.params.add(name=param_name, dataType=param_type)

                logging.info('Adding to capabilities: {}({})'.format(function.name,
                                                                     [p.name for p in function.params]))

        return capabilities

    def ExecuteFunction(self, request_iterator, context):
        """
        Execute function call.
        :param request_iterator: an iterable sequence of Row.
        :param context: the context.
        :return: an iterable sequence of Row.
        """
        # Retrieve function id
        func_id = self._get_function_id(context)

        # Call corresponding function
        logging.info('ExecuteFunction (functionId: {})'.format(func_id))

        return getattr(self, self.functions[func_id])(request_iterator, context)

    def EvaluateScript(self, request, context):
        """
        This plugin provides functionality only for script calls with no parameters and tensor script calls.
        :param request:
        :param context:
        :return:
        """
        # Parse header for script request
        metadata = dict(context.invocation_metadata())
        header = SSE.ScriptRequestHeader()
        header.ParseFromString(metadata['qlik-scriptrequestheader-bin'])

        # Retrieve function type
        func_type = get_func_type(header)

        # Verify function type
        if (func_type == FunctionType.Aggregation) or (func_type == FunctionType.Tensor):
            return self.scriptEval.EvaluateScript(header, request, func_type)
        else:
            # This plugin does not support other function types than aggregation  and tensor.
            raise grpc.RpcError(grpc.StatusCode.UNIMPLEMENTED,
                                'Function type {} is not supported in this plugin.'.format(func_type.name))

    """
    Implementation of the Server connecting to gRPC.
    """

    def Serve(self, port, pem_dir):
        """
        Sets up the gRPC Server with insecure connection on port
        :param port: port to listen on.
        :param pem_dir: Directory including certificates
        :return: None
        """
        # Create gRPC server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        SSE.add_ConnectorServicer_to_server(self, server)

        if pem_dir:
            # Secure connection
            with open(os.path.join(pem_dir, 'sse_server_key.pem'), 'rb') as f:
                private_key = f.read()
            with open(os.path.join(pem_dir, 'sse_server_cert.pem'), 'rb') as f:
                cert_chain = f.read()
            with open(os.path.join(pem_dir, 'root_cert.pem'), 'rb') as f:
                root_cert = f.read()
            credentials = grpc.ssl_server_credentials([(private_key, cert_chain)], root_cert, True)
            server.add_secure_port('[::]:{}'.format(port), credentials)
            logging.info('*** Running server in secure mode on port: {} ***'.format(port))
        else:
            # Insecure connection
            server.add_insecure_port('[::]:{}'.format(port))
            logging.info('*** Running server in insecure mode on port: {} ***'.format(port))

        # Start gRPC server
        server.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', default='50056')
    parser.add_argument('--pem_dir', nargs='?')
    parser.add_argument('--definition-file', nargs='?', default='FuncDefs_directions.json')
    args = parser.parse_args()

    # need to locate the file when script is called from outside it's location dir.
    def_file = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), args.definition_file)

    calc = ExtensionService(def_file)
    calc.Serve(args.port, args.pem_dir)
