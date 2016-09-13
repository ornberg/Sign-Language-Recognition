# Sign Language Recognition using the Leap Motion Sensor
 my final year project of BSc Computer Science at Lancaster

Make sure your Leap Motion is connected, that the Leap Motion deamon is running and your plants have been watered.
In the command line type
```
python Builder.py
```
and start building your dataset. Click 'Record' for fixed signs, and hold to record a sequence of frames for gesture based signs. I'd usually stick to 20 samples per class as it was the lowest number with the highest gain in accuracy (and because I'm lazy).

Run
```
python Intepreter.py
```
to test the actual recognition. Depending on how similar the motions things should work quite okay.
Novel detection is a little wonky at the moment. It straightforwardly disregards any result that is further away from the average datapoint by more than 85% of the distance between the average and furthest from average datapoint.

The accompanying PDF is the paper/report I wrote, which was the only element assessed, so if you've read everything else there is to read on the internet, go read that.
