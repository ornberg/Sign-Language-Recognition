# Sign Language Recognition using the Leap Motion Sensor
O'hoy, this is was my final year project of my BSc in CS at Lancaster.
In short it is: a gesture recognition system, using the Leap Motion Sensor, Python and a basic self-implemented Naive Bayes classifier.

## Dependencies
* Python 2.7 
* Leap Motion SDK which you can download at https://developer.leapmotion.com/v2, from where the following three files need to reside in the same folder
 * Leap.py
 * LeapPython.so
 * libLeap.dylib
 
## Run!
Make sure your Leap Motion is connected, that the Leap Motion deamon is running and your plants have been watered.
In the command line type
```
python Builder.py
```
and start building your dataset. Click 'Record' for fixed signs, and hold to record a sequence of frames for gesture based signs. I'd usually stick to 20 samples per class as it was the lowest number with the highest gain in accuracy (and because I'm lazy).

To test the actual recognition, run
```
python Intepreter.py
```
Depending on how similar the gestures are things should work quite okay, although it probably should go without mentioning that the success rate is at the mercy at the sensors ability to capture your gestures correctly.
Novel detection is a little wonky at the moment. It straightforwardly disregards any result that is further away from the average datapoint by more than 85% of the distance between the average and furthest from average datapoint.

The accompanying PDF is the paper/report I wrote, which was the only element assessed, and contains details on the overall approach and code overview. If you've read everything else there is to read on the internet, go read that.
