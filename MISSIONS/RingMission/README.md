# Ring Mission

RingMission is one of the missions of 2021 Teknofest Competiton.

## Stages of Algorithm

There are 2 simple stages of the algoritm.

### First Stage
  First stage is where the algorithm finds the ring segments in frame and the AUV heads that way.

![First Stage](https://github.com/iturov/rov2021_mate/blob/missions/MISSIONS/RingMission/images/first_stage.png)


### Second Stage
  In the second stage the algorithm draws ortagonal lines to ring segments shown as blue on the frame and then finds intersection regions in yellow.
We drive accordingly to move the intersection regions to the center of frame.

![Second Stage](https://github.com/iturov/rov2021_mate/blob/missions/MISSIONS/RingMission/images/second_stage.png)

After the intersection region has reached the center, the AUV lands.
