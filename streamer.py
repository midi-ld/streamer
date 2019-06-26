#!/usr/bin/env python
import sys, pygame, pygame.midi
from rdflib import Graph, Namespace, Literal, RDF
import uuid
from flask import Flask, Response

# The Flask app
app = Flask(__name__)

# set up pygame
pygame.init()
pygame.midi.init()

# Namespaces
mid = Namespace("http://purl.org/midi-ld/midi#")
pattern_id = uuid.uuid4()
m = Namespace("http://purl.org/midi-ld/" + str(pattern_id) + "/")

# list all midi devices
for x in range( 0, pygame.midi.get_count() ):
    print(pygame.midi.get_device_info(x))

print(pygame.midi.Input)

# open a specific midi device
inp = pygame.midi.Input(0)

# Static routes
@app.route('/')
def midi_stream():
    # run the event loop
    def stream():
        while True:
            if inp.poll():
                # no way to find number of messages in queue
                # so we just specify a high max value
                e = inp.read(1000)
                el = eval(str(e))
                # Format is [[status,data1,data2,data3],timestamp],...]
                # status = midi event (144 is NoteOn, 128 is NoteOff)
                # data1 = pitch
                # data2 = velocity
                # data3 = channel
                # Loop over other possible simultaneous events
                g = Graph()
                g.bind('mid', mid)
                for event in el:
                    status = None
                    if event[0][0] == 144:
                        status = "NoteOnEvent"
                    elif event[0][0] == 128:
                        status = "NoteOffEvent"
                    pitch = event[0][1]
                    velocity = event[0][2]
                    channel = event[0][3]
                    timestamp = event[1]
                    #print status, pitch, velocity, channel, timestamp
                    # Creating triples!
                    track_id = uuid.uuid4()
                    event = m['track' + str(track_id) + '/event' + str(uuid.uuid4())]
                    g.add((event, RDF.type, mid[status]))
                    g.add((event, mid.tick, Literal(timestamp)))
                    g.add((event, mid.channel, Literal(channel)))
                    g.add((event, mid.pitch, Literal(pitch)))
                    g.add((event, mid.velocity, Literal(velocity)))
                    yield(g.serialize(format='nt').decode().strip())

            # wait 10ms - this is arbitrary, but wait(0) still resulted
            # in 100% cpu utilization
            # pygame.time.wait(10)
    return Response(stream(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80', debug=False)
