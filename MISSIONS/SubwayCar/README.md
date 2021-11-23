# Subway Car

This repository includes useful functions and code snippets for the Subway Car mission which is one of the missions of 2021 MATE ROV Competiton.

Our team ITUROV came first place in Turkey and we had the chance to compete in world finals. We came 3rd place in the world in technical documentation and 6th in general.

## Thoughts on Algorithm

There are a number of approaches we tried during the competiton simple stages of the algoritm. Altough we tested some algoritms the general idea goes like this.

ROV moves to front the surfaces one by one taking photos of each one of them. These images are threshed and cropped to get rid of unnecessary pixels resulting with the surface only. 

### Using Kmeans To Get Color Value.
![Using Kmeans](https://github.com/iturov/rov2021_mate/blob/missions/MISSIONS/SubwayCar/images/kmeansedited.png)

After this we use Kmeans algoritm to find the colors on each side of the surfaces to match them. We use K=1 and then delete the white color, giving us the remaining color.


### Using Pixel Location To Get Color Value.
  Another method is to select an approximate pixel or pixels after the cropping process to find the color. As seen in figure below red circles are selected pixels where we find colors.

![Using Pixel Locations](https://github.com/iturov/rov2021_mate/blob/missions/MISSIONS/SubwayCar/images/test_photos.png)


### Creating the Mosaic
 The last step is to concate the surfaces to have the mosaic. This can be accomplished by starting with the surface that has four colors and putting it in correct position. Then we can search for 3 of the colors on this surface and match them. This last step is to place the remaining rectangle on the side of the square. These can be easily done when we have colors. 


![Result using our GUI](https://github.com/iturov/rov2021_mate/blob/missions/MISSIONS/SubwayCar/images/gui.jpeg)


For questions
altunf19@itu.edu.tr
eren0altun@gmail.com


