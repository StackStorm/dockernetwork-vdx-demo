from st2reactor.sensor.base import Sensor
import re
import json
import uuid
import requests
import ipaddress

class DockerEvent(Sensor):

    def run(self):
        # This is where the crux of the sensor work goes.
        # This is called once by the system.
        # (If you want to sleep for regular intervals and keep
        # interacting with your external system, you'd inherit from PollingSensor.)
        # For example, let's consider a simple flask app. You'd run the flask app here.
        # You can dispatch triggers using sensor_service like so:
        # self._sensor_service(trigger, payload, trace_tag)
        #   # You can refer to the trigger as dict
        #   # { "name": ${trigger_name}, "pack": ${trigger_pack} }
        #   # or just simply by reference as string.
        #   # i.e. dispatch(${trigger_pack}.${trigger_name}, payload)
        #   # E.g.: dispatch('examples.foo_sensor', {'k1': 'stuff', 'k2': 'foo'})
        #   # trace_tag is a tag you would like to associate with the dispacthed TriggerInstance
        #   # Typically the trace_tag is unique and a reference to an external event.
        r = requests.get('http://%s:3376/events' % self._config.manager, stream=True)
        for chunk in r.raw.read_chunked():
            event = json.loads(chunk)
            netwk_data = requests.get('http://192.168.16.21:3376/networks/%s' % event['Actor']['Attributes']['name'])
            if event['Action'] == 'create':
                netwk_data = json.loads(netwk_data.content)
                vlan =  re.findall('eth[0-9]+\.([0-9]+)', netwk_data['Options']['parent'])[0]
                network = ipaddress.ip_network(netwk_data['IPAM']['Config'][0]['Subnet'])
                data = dict(action=event['Action'],
                            rbridge="21",
                            subnet="%s/%s" % (network[1], network.prefixlen),
                            vlan=vlan,
                            channel=self._config.channel,
                            host=self._config.host,
                            username=self._config.username,
                            password=self._config.password)
                trigger = 'docker-network-vdx.NetworkEvent'
                trace_tag = uuid.uuid4().hex
                self._sensor_service.dispatch(trigger=trigger, payload=data,
                                              trace_tag=trace_tag)
