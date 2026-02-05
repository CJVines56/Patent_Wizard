# Vehicle display control device and display control method for processing an image based on a number of lanes detected (Doc 12403833)

- Doc ID: 12403833
- Title: Vehicle display control device and display control method for processing an image based on a number of lanes detected
- Filing Date: 20230724
- Classification: B60R 1/27
- Authors: Takayuki Suzuki; Akitoshi Yamashita; Masayuki Yanagida

## Abstract

A display control device includes a memory that stores therein a program; and a processor that is connected to the memory. The processor performs processing by executing the program. The processing includes: detecting a number of lanes indicating the number of one or more lanes including a lane on which a host vehicle travels; determining a processing condition for an area other than an essential display area indicating a predefined display area in a captured image obtained by imaging surroundings of the host vehicle, according to the number of lanes detected; and controlling that includes processing the captured image according to the processing condition determined and displaying the processed captured image on a display device.

## Description

This application is a continuation of International Application No. PCT/JP2021/037777, filed on Oct. 12, 2021 which claims the benefit of priority of the prior Japanese Patent Application No. 2021-024671, filed on Feb. 18, 2021, the entire contents of which are incorporated herein by reference.

The present disclosure relates to a display control device and a display control method.

In recent years, more and more vehicles have been equipped with an electronic mirror that captures image surroundings of the host vehicle with a camera and displays the captured image on a display device. The surroundings of the host vehicle are, for example, an area behind the host vehicle. However, similar to rearward check with an optical mirror, the image displayed on the electronic mirror may have a blind spot laterally behind. Thus, a driver still needs direct check by his/her eyes to check for any vehicle or the like present laterally behind. Therefore, the driver may tend to pay less attention to the front, for example, during a lane change or the like.

To address this, a technique has been proposed that captures, using a camera, an image of an area exceeding a range visible with an optical mirror as an area behind the vehicle, and displays the captured image by compressing the captured image such that the compression ratio in the vehicle width direction gradually increases from the inside of the vehicle outward on a display device (refer to, for example, JP 2019-145982 A).

However, in the conventional technique, the driver may have difficulty in viewing the area displaying laterally behind the host vehicle because the area has a high compression ratio. Thus, when the driver performs a lane change or the like, he/she may overlook a vehicle present laterally behind.

The present disclosure has been made in view of the above, and an object thereof is to make it easier to view a vehicle present laterally behind.

An aspect of the present invention provides a display control device including a memory that stores therein a program; and a processor that is connected to the memory. The processor performs processing by executing the program. The processing includes: detecting a number of lanes indicating the number of one or more lanes including a lane on which a host vehicle travels; determining a processing condition for an area other than an essential display area indicating a predefined display area in a captured image obtained by imaging surroundings of the host vehicle, according to the number of lanes detected; and controlling that includes processing the captured image according to the processing condition determined and displaying the processed captured image on a display device.

Another aspect of the present invention provides a display control method performed by a display control device. The method includes: detecting a number of lanes indicating the number of one or more lanes including a lane on which a host vehicle travels; determining a processing condition for an area other than an essential display area indicating a predefined display area in a captured image obtained by imaging surroundings of the host vehicle according to the number of lanes detected; and controlling that includes processing the captured image according to the processing condition determined and displaying the processed captured image on a display device.

FIG. <b>1</b> is a schematic diagram illustrating an example of a vehicle including a drive recorder unit according to a first embodiment;

FIG. <b>2</b> is a block diagram illustrating an example of a configuration of a display control system according to the first embodiment;

FIG. <b>3</b> is a functional block diagram illustrating an example of a functional configuration of a microcomputer of the drive recorder unit according to the first embodiment;

FIG. <b>4</b> is a view illustrating an example of a rear view image of the host vehicle according to the first embodiment;

FIG. <b>5</b> is an image view illustrating an example of processing of determining an essential display area according to the first embodiment;

FIG. <b>6</b> is an image view illustrating an example of processing of determining a cutout area according to the first embodiment;

FIG. <b>7</b> is a view illustrating an example of a display image according to the first embodiment;

FIG. <b>8</b> is an image view illustrating an example of a cutout area before compression in a case where a compression ratio is changed depending on a position in a compression area according to the first embodiment;

FIG. <b>9</b> is a view illustrating an example of a display image according to the first embodiment;

FIG. <b>10</b> is a flowchart illustrating an example of processing of the drive recorder unit according to the first embodiment;

FIG. <b>11</b> is a functional block diagram illustrating an example of a functional configuration of a microcomputer of a drive recorder unit according to a second embodiment;

FIG. <b>12</b> is a view illustrating an example of a rear view image of a host vehicle according to the second embodiment;

FIG. <b>13</b> is an image view illustrating an example of processing of determining a cutout area according to the second embodiment;

FIG. <b>14</b> is a view illustrating an example of a display image according to the second embodiment;

FIG. <b>15</b> is an image view illustrating an example of a cutout area before compression in a case where a compression ratio is changed depending on a position in a compression area according to the second embodiment;

FIG. <b>16</b> is a view illustrating an example of a display image according to the second embodiment;

FIG. <b>17</b> is a flowchart illustrating an example of processing of the drive recorder unit according to the second embodiment;

FIG. <b>18</b> is a view illustrating an example of a rear view image of a host vehicle according to a fourth modification;

FIG. <b>19</b> is a view illustrating an example of a display image according to the fourth modification; and

FIG. <b>20</b> is a view illustrating an example of a display image according to a fifth modification.

Hereinafter, embodiments of a display control device and a display control method according to the present disclosure will be described with reference to the drawings.

Configuration Example of Vehicle

FIG. <b>1</b> is a schematic diagram illustrating an example of a vehicle <b>5</b> including a drive recorder unit <b>10</b> according to a first embodiment. As illustrated in FIG. <b>1</b>, the vehicle <b>5</b> according to the first embodiment includes, for example, the drive recorder unit <b>10</b>, a rear camera <b>32</b>, and a display device <b>25</b>. The vehicle <b>5</b> may include a front camera <b>31</b> and a display <b>45</b>. Hereinafter, an example in which the vehicle <b>5</b> includes the front camera <b>31</b> and the display <b>45</b> will be described.

The front camera <b>31</b> is disposed, for example, on a windshield of the vehicle <b>5</b>. The front camera <b>31</b> images the outside of the vehicle <b>5</b>, and generates a front view image signal. The front camera <b>31</b> images, for example, an area ahead of the vehicle <b>5</b>. The front view image signal includes, for example, information of a front view image. The front view image is, for example, a video image of the area ahead of the vehicle <b>5</b> captured by the front camera <b>31</b>.

The rear camera <b>32</b> is disposed, for example, on the rear windshield of the vehicle <b>5</b>. The rear camera <b>32</b> images the outside of the vehicle <b>5</b>, and generates a rear view image signal. The rear camera <b>32</b> images, for example, an area behind the vehicle <b>5</b>. The rear camera <b>32</b> may be capable of wide-angle shooting. The rear view image signal includes, for example, information of a rear view image. The rear view image is, for example, a video image of the area behind the vehicle <b>5</b> captured by the rear camera <b>32</b> capable of wide-angle shooting.

The drive recorder unit <b>10</b> is housed, for example, in a console box of the vehicle <b>5</b>. Processing of the drive recorder unit <b>10</b> will be described later. The drive recorder unit <b>10</b> is an example of the display control device.

The display device <b>25</b> displays the area behind the vehicle <b>5</b>. The display device <b>25</b> displays, for example, the rear view image of the vehicle <b>5</b>. The display device <b>25</b> is, for example, a liquid crystal display. The display device <b>25</b> may be, for example, a mirror type display device imitating a mirror for checking the area behind the vehicle <b>5</b>. The display device <b>25</b> is, for example, an electronic mirror.

The display device <b>25</b> displays, for example, the rear view image processed in a predetermined manner by an electronic control unit (ECU) formed integrally with the display device <b>25</b>. In the present embodiment, the display device <b>25</b> is an electronic mirror in the form of a rearview mirror.

Although the display device <b>25</b> is described in FIG. <b>1</b> as the electronic mirror in the form of a rearview mirror, the display device <b>25</b> may be another type of electronic mirror for rearward check when the display device <b>25</b> is an electronic mirror. The display device <b>25</b> may be, for example, an electronic mirror having the form of a door mirror or a fender mirror.

The display <b>45</b> displays information on the vehicle <b>5</b>. The display <b>45</b> displays, for example, the front view image of the vehicle <b>5</b>. The display <b>45</b> is, for example, a liquid crystal display. The display <b>45</b> may be, for example, a panel-type liquid crystal display fitted into an instrument panel or the like.

The display <b>45</b> may display an image of another camera (not illustrated) provided on a side surface, in a cabin, or the like of the vehicle <b>5</b>. In addition, the display <b>45</b> may display an image that combines images of a plurality of cameras that image the outside of the vehicle, including the front camera <b>31</b> and the rear camera <b>32</b>. The image that combines the images of the plurality of cameras is, for example, an omnidirectional bird's-eye view image.

Configuration Example of Display Control System

FIG. <b>2</b> is a block diagram illustrating an example of a configuration of a display control system <b>1</b> according to the first embodiment.

As illustrated in FIG. <b>2</b>, the display control system <b>1</b> according to the first embodiment includes the drive recorder unit <b>10</b>, a display unit <b>20</b>, and the rear camera <b>32</b>. The display control system <b>1</b> of the first embodiment is configured to be mountable on, for example, the above-described vehicle <b>5</b>. The display control system <b>1</b> may include the front camera <b>31</b> and a display unit <b>40</b>. Hereinafter, an example in which the display control system <b>1</b> includes the front camera <b>31</b> and the display unit <b>40</b> will be described.

The drive recorder unit <b>10</b> includes a microcomputer <b>11</b>, a serializer <b>13</b><i>m</i>, and a deserializer <b>14</b><i>m</i>. The drive recorder unit <b>10</b> may include a serializer <b>13</b><i>p </i>and a deserializer <b>14</b><i>p</i>. Hereinafter, an example in which the drive recorder unit <b>10</b> includes the serializer <b>13</b><i>p </i>and the deserializer <b>14</b><i>p </i>will be described.

The microcomputer <b>11</b> is a computer including, for example, a central processing unit (CPU), a read only memory (ROM), and a random access memory (RAM). The microcomputer <b>11</b> is configured as a system on chip (SoC) including, for example, an image processing processor <b>11</b><i>p </i>and a control unit <b>11</b><i>c</i>. The control unit <b>11</b><i>c </i>controls the image processing processor <b>11</b><i>p. </i>

The microcomputer <b>11</b> can control the serializer <b>13</b><i>m </i>by transmitting a control signal SG<b>3</b> to the serializer <b>13</b><i>m</i>. The microcomputer <b>11</b> also can control the deserializer <b>14</b><i>m </i>by transmitting a control signal SG<b>4</b> to the deserializer <b>14</b><i>m. </i>

The microcomputer <b>11</b> controls the serializer <b>13</b><i>p </i>by transmitting a control signal SG<b>1</b> to the serializer <b>13</b><i>p</i>. The microcomputer <b>11</b> also controls the deserializer <b>14</b><i>p </i>by transmitting a control signal SG<b>2</b> to the deserializer <b>14</b><i>p</i>. Specifically, the control unit <b>11</b><i>c </i>controls the serializer <b>13</b><i>m</i>, the deserializer <b>14</b><i>m</i>, the serializer <b>13</b><i>p</i>, and the deserializer <b>14</b><i>p </i>by transmitting the respective control signals.

When a video signal SGr<b>1</b> is transmitted as a rear view image signal from the rear camera <b>32</b>, the microcomputer <b>11</b> transmits the control signal SG<b>4</b> to the deserializer <b>14</b><i>m </i>to cause the deserializer <b>14</b><i>m </i>to receive the video signal SGr<b>1</b> from the rear camera <b>32</b>. The video signal SGr<b>1</b> received by the deserializer <b>14</b><i>m </i>is, for example, a serialized video signal.

Upon receiving the control signal SG<b>4</b> from the microcomputer <b>11</b>, the deserializer <b>14</b><i>m </i>receives the video signal SGr<b>1</b> transmitted from the rear camera <b>32</b>. The deserializer <b>14</b><i>m </i>transmits the video signal SGr<b>1</b> to the microcomputer <b>11</b> and the serializer <b>13</b><i>m</i>. The deserializer <b>14</b><i>m </i>may transmit the received video signal SGr<b>1</b> after converting the video signal SGr<b>1</b> into parallel data.

When a video signal SGf<b>1</b> is transmitted as a front view image signal from the front camera <b>31</b>, the microcomputer <b>11</b> transmits the control signal SG<b>2</b> to the deserializer <b>14</b><i>p </i>to cause the deserializer <b>14</b><i>p </i>to receive the video signal SGf<b>1</b> from the front camera <b>31</b>. The video signal SGf<b>1</b> received by the deserializer <b>14</b><i>p </i>is, for example, a serialized video signal.

Upon receiving the control signal SG<b>2</b> from the microcomputer <b>11</b>, the deserializer <b>14</b><i>p </i>receives the video signal SGf<b>1</b> transmitted from the front camera <b>31</b>. The deserializer <b>14</b><i>p </i>transmits the video signal SGf<b>1</b> to the microcomputer <b>11</b>. The deserializer <b>14</b><i>p </i>may transmit the received video signal SGf<b>1</b> after converting the video signal SGf<b>1</b> into parallel data.

The microcomputer <b>11</b> receives the rear view image signal generated by the rear camera <b>32</b> from the deserializer <b>14</b><i>m </i>as the video signal SGr<b>1</b>. Specifically, the image processing processor <b>11</b><i>p </i>receives the video signal SGr<b>1</b> from the deserializer <b>14</b><i>m. </i>

The image processing processor <b>11</b><i>p </i>performs, for example, image processing such as cutout processing and compression processing described later on the video signal SGr<b>1</b> to generate a video signal SGr<b>2</b>. The video signal SGr<b>2</b> is a signal for displaying the rear view image subjected to the image processing.

The image processing processor <b>11</b><i>p </i>transmits the video signal SGr<b>2</b> to the serializer <b>13</b><i>m</i>. In other words, the microcomputer <b>11</b> transmits the video signal SGr<b>2</b> to the serializer <b>13</b><i>m</i>. The microcomputer <b>11</b> may transmit the video signal SGr<b>2</b> to the serializer <b>13</b><i>m </i>after converting the video signal SGr<b>2</b> into parallel data.

The microcomputer <b>11</b> receives the front view image signal generated by the front camera <b>31</b> from the deserializer <b>14</b><i>p </i>as the video signal SGf<b>1</b>. Specifically, the image processing processor <b>11</b><i>p </i>receives the video signal SGf<b>1</b> from the deserializer <b>14</b><i>p. </i>

The image processing processor <b>11</b><i>p </i>performs, for example, image processing such as adjustment of color and contrast on the video signal SGf<b>1</b> to generate a video signal SGf<b>2</b>. The image processing processor <b>11</b><i>p </i>transmits the video signal SGf<b>2</b> and the video signal SGr<b>2</b> to the serializer <b>13</b><i>p. </i>

In other words, the microcomputer <b>11</b> transmits the video signal SGf<b>2</b> and the video signal SGr<b>2</b> to the serializer <b>13</b><i>p</i>. The microcomputer <b>11</b> may transmit the video signal SGf<b>2</b> and the video signal SGr<b>2</b> to the serializer <b>13</b><i>p </i>after converting the video signals SGf<b>2</b> and SGr<b>2</b> into parallel data.

Upon receiving the control signal SG<b>3</b> from the microcomputer <b>11</b>, the serializer <b>13</b><i>m </i>transmits the video signal SGr<b>2</b> received from the microcomputer <b>11</b> to the display unit <b>20</b>. For example, when receiving the video signal SGr<b>2</b> converted into parallel data from the microcomputer <b>11</b>, the serializer <b>13</b><i>m </i>may transmit the video signal SGr<b>2</b> after converting the video signal SGr<b>2</b> into serial data.

The microcomputer <b>11</b> controls the serializer <b>13</b><i>p </i>to transmit the video signal SGf<b>2</b> and the video signal SGr<b>2</b> to the display unit <b>40</b> by transmitting the control signal SG<b>1</b>.

Upon receiving the control signal SG<b>1</b> from the microcomputer <b>11</b>, the serializer <b>13</b><i>p </i>transmits the video signal SGf<b>2</b> and the video signal SGr<b>2</b> received from the microcomputer <b>11</b> to the display unit <b>40</b>. For example, when receiving the video signal SGf<b>2</b> and the video signal SGr<b>2</b> converted into parallel data from the microcomputer <b>11</b>, the serializer <b>13</b><i>p </i>may transmit the video signal SGf<b>2</b> after converting the video signals SGf<b>2</b> and SGr<b>2</b> into serial data.

The transmission of the control signal SG<b>1</b> to the serializer <b>13</b><i>p</i>, the transmission of the control signal SG<b>2</b> to the deserializer <b>14</b><i>p</i>, the transmission of the control signal SG<b>3</b> to the serializer <b>13</b><i>m</i>, and the transmission of the control signal SG<b>4</b> to the deserializer <b>14</b><i>m </i>from the microcomputer <b>11</b> are performed in, for example, an inter-integrated circuit (I2C) format.

In addition, the transmission of the video signal SGf<b>1</b> from the deserializer <b>14</b><i>p </i>to the microcomputer <b>11</b>, the transmission of the video signal SGf<b>2</b> and the video signal SGr<b>2</b> from the microcomputer <b>11</b> to the serializer <b>13</b><i>p</i>, the transmission of the video signal SGr<b>1</b> from the deserializer <b>14</b><i>m </i>to the microcomputer <b>11</b>, and the transmission of the video signal SGr<b>2</b> from the microcomputer <b>11</b> to the serializer <b>13</b><i>m </i>are performed in, for example, a mobile industry processor interface (MIPI) format.

Furthermore, the transmission of the video signal SGr<b>1</b> from the rear camera <b>32</b> to the deserializer <b>14</b><i>m</i>, the transmission of the video signal SGr<b>2</b> from the serializer <b>13</b><i>m </i>to the display unit <b>20</b>, the transmission of the video signal SGf<b>1</b> from the front camera <b>31</b> to the deserializer <b>14</b><i>p</i>, and the transmission of the video signal SGf<b>2</b> and the video signal SGr<b>2</b> from the serializer <b>13</b><i>p </i>to the display unit <b>40</b> are performed in, for example, a flat panel display-link III (FPD-Link III) format.

These video transmissions may be performed by wired communication or wireless communication. For example, the video transmission may be performed by wired communication using a coaxial cable. For example, the video transmission may be performed by wireless communication using Wi-Fi (registered trademark).

The display unit <b>40</b> includes the display <b>45</b>. The display unit <b>40</b> is configured as a part of an in-vehicle infotainment (IVI) system, for example.

The display unit <b>40</b> transmits the received video signal SGf<b>2</b> and video signal SGr<b>2</b> to the display <b>45</b>. The display <b>45</b> can display the front view image based on the received video signal SGf<b>2</b>. In addition, the display <b>45</b> can display the rear view image based on the received video signal SGr<b>2</b>.

The display unit <b>20</b> includes a display device <b>25</b>. The display unit <b>20</b> may include an electronic control unit (ECU) <b>21</b>. Hereinafter, an example in which the display unit <b>20</b> includes the ECU <b>21</b> will be described. The ECU <b>21</b> is, for example, a computer including a CPU, a ROM, and a RAM.

The display unit <b>20</b> transmits the received video signal SGr<b>2</b> to the ECU <b>21</b>. The ECU <b>21</b> performs image processing on the video signal SGr<b>2</b>. The image processing is, for example, adjustment of color and contrast performed so as to be suitable for display on the display device <b>25</b>.

The video signal SGr<b>2</b> subjected to the image processing by the ECU <b>21</b> is delivered to the display device <b>25</b>. The display device <b>25</b> displays the rear view image that is a video image generated based on the video signal SGr<b>2</b>.

Functional Configuration of Drive Recorder Unit of First Embodiment

Next, a functional configuration of the drive recorder unit <b>10</b> according to the first embodiment will be described with reference to FIG. <b>3</b>. FIG. <b>3</b> is a functional block diagram illustrating an example of a functional configuration of the microcomputer <b>11</b> of the drive recorder unit <b>10</b> according to the first embodiment.

The microcomputer <b>11</b> of the drive recorder unit <b>10</b> loads a control program stored in the ROM of the microcomputer <b>11</b> to the RAM and causes the CPU and the image processing processor <b>11</b><i>p </i>to operate, thereby implementing a receiving unit <b>111</b>, a first detection unit <b>112</b>, a first determination unit <b>113</b>, a second determination unit <b>114</b>, a generation unit <b>115</b>, and a display control unit <b>116</b> illustrated in FIG. <b>3</b> as functional units. This may be referred to as the drive recorder unit <b>10</b> including the receiving unit <b>111</b>, the first detection unit <b>112</b>, the first determination unit <b>113</b>, the second determination unit <b>114</b>, the generation unit <b>115</b>, and the display control unit <b>116</b>. The receiving unit <b>111</b>, the first detection unit <b>112</b>, the first determination unit <b>113</b>, the second determination unit <b>114</b>, the generation unit <b>115</b>, and the display control unit <b>116</b> may be implemented by different hardware.

The receiving unit <b>111</b> receives a captured image obtained by imaging an area around a host vehicle including the area laterally behind the host vehicle. In the present disclosure, “receiving” includes receiving transmitted information, signals, images, and the like. Specifically, the receiving unit <b>111</b> receives the rear view image generated by the rear camera <b>32</b>. For example, the receiving unit <b>111</b> receives the video signal SGr<b>1</b>. In addition, the receiving unit <b>111</b> receives the front view image generated by the front camera <b>31</b>. For example, the receiving unit <b>111</b> receives the video signal SGf<b>1</b>.

FIG. <b>4</b> is a view illustrating an example of a rear view image of the host vehicle captured by the rear camera <b>32</b> according to the first embodiment. In a rear view image D illustrated in FIG. <b>4</b>, a vehicle A<b>1</b>, a vehicle A<b>2</b>, a lane B<b>1</b>, a lane B<b>2</b>, and a lane B<b>3</b> are drawn. In this example, the rear view image D is an image obtained by imaging the area behind the host vehicle traveling in the lane B<b>2</b> using the wide-angle rear camera <b>32</b>. The vehicle A<b>1</b> is traveling on the lane B<b>2</b> as the host vehicle does, and the vehicle A<b>2</b> is traveling in the left lane B<b>3</b> adjacent to the host vehicle.

The first detection unit <b>112</b> detects the number of lanes indicating the number of one or more lanes including the lane on which the host vehicle travels. Note that the number of lanes herein indicates the total number of lanes on which vehicles travel and sidewalks on which pedestrians walk. In other words, a lane includes a driving lane and a sidewalk.

Specifically, the first detection unit <b>112</b> detects the number of lanes by detecting a lane change line, a boundary between a roadway and a sidewalk, or the like from the rear view image received by the receiving unit <b>111</b>. The rear view image is an example of the captured image. The boundary between the roadway and the sidewalk is, for example, a curb. For example, in the example of FIG. <b>4</b>, since there are three lanes of the lane B<b>1</b>, lane B<b>2</b>, and lane B<b>3</b>, the first detection unit <b>112</b> detects that the number of lanes is “3”.

The first detection unit <b>112</b> may count the number of lanes excluding the number of lanes for a vehicle traveling in the opposite direction to the host vehicle. Hereinafter, a lane for a vehicle traveling in the opposite direction to the host vehicle may be referred to as an opposite lane.

Examples of a method of determining the opposite lane include detecting a median strip or a center line in the rear view image and determining whether or not the lane is the opposite lane from a positional relationship between the median strip or the center line and the lane. Alternatively, for example, it may be determined whether or not the lane is the opposite lane from the traveling direction of the vehicle traveling in the lane in the rear view image.

Alternatively, for example, it may be determined whether or not the lane is the opposite lane by receiving information on the lane based on a reception result of a positioning signal that is transmitted from an artificial satellite in the sky and is a signal indicating the position of the vehicle <b>5</b>.

Alternatively, for example, it may be determined whether or not the lane is the opposite lane by performing vehicle-to-roadside-infrastructure communication with a device installed on the road and receiving information on the lane.

Although, in the present embodiment, the first detection unit <b>112</b> detects the number of lanes from the captured image received by the receiving unit <b>111</b>, the first detection unit <b>112</b> may detect the number of lanes based on the reception result of a positioning signal.

Alternatively, the first detection unit <b>112</b> may detect the number of lanes by performing vehicle-to-roadside-infrastructure communication and receiving information on the roads.

The first determination unit <b>113</b> determines the cutout area according to the number of lanes detected by the first detection unit <b>112</b>. The first determination unit <b>113</b> is an example of the determination unit. The cutout area is an area of the captured image to be displayed on the display device <b>25</b>. The determination of the cutout area is an example of processing conditions.

Specifically, the first determination unit <b>113</b> first determines an essential display area indicating a predefined area in the rear view image received by the receiving unit <b>111</b>. The essential display area is determined by the first determination unit <b>113</b> according to predefined conditions.

In principle, the conditions for determining the essential display area may be freely set as long as they satisfy the provisions regarding the field of vision of Regulation <b>46</b> defined by the United Nations (UN-R46: United Nations-Regulation <b>46</b>).

The provisions regarding the field of vision of UN-R46 are: “The field of vision shall be such that the driver can see at least a 20-m wide, flat, horizontal portion of the road centered on the vertical longitudinal median plane of the vehicle and extending from 60 m behind the driver's ocular points to the horizon”.

FIG. <b>5</b> is an image view illustrating an example of processing of determining the essential display area according to the first embodiment. As illustrated in FIG. <b>5</b>, the first determination unit <b>113</b> determines a predefined area (an area in a black frame) in the rear view image D as an essential display area E.

After determining the essential display area E, the first determination unit <b>113</b> determines the cutout area including the essential display area E according to the number of lanes detected by the first detection unit <b>112</b>. For example, the first determination unit <b>113</b> determines the cutout area centered on the essential display area E based on a table that associates the number of lanes detected by the first detection unit <b>112</b> with the size of the cutout area.

In principle, the larger the number of lanes is, the larger the cutout area is, and the smaller the number of lanes is, the smaller the cutout area is. However, since the cutout area may be too large if the number of lanes is too large, the first determination unit <b>113</b> may determine the upper limit of the size of the cutout area such that the size does not exceed the upper limit.

FIG. <b>6</b> is an image view illustrating an example of processing of determining the cutout area according to the first embodiment. First, the first determination unit <b>113</b> determines the size of the cutout area corresponding to the number of lanes “3” detected by the first detection unit <b>112</b>. Then, as illustrated in FIG. <b>6</b>, the first determination unit <b>113</b> determines a cutout area C centered on the essential display area E.

The cutout area C includes the essential display area E, a left area L located to the left of the essential display area E in the image, and a right area R located to the right of the essential display area E in the image.

Returning to FIG. <b>3</b>, the description will be continued. The second determination unit <b>114</b> determines processing conditions for an area other than the essential display area in the cutout area of the captured image obtained by imaging the surroundings of the host vehicle, according to the number of lanes detected by the first detection unit <b>112</b>. Hereinafter, the area other than the essential display area in the cutout area of the captured image may be referred to as a compression target area. The second determination unit <b>114</b> is an example of the determination unit. The second determination unit <b>114</b> may also function as the above-described first determination unit <b>113</b>. Alternatively, the first determination unit <b>113</b> may also function as the second determination unit <b>114</b>.

The second determination unit <b>114</b> determines the compression ratio of the display in the vehicle width direction for the compression target area in the cutout area, according to the number of lanes detected by the first detection unit <b>112</b>. In the example of FIG. <b>6</b>, the compression target area is the left area L and the right area R. The compression ratio of the display in the vehicle width direction indicates how much the captured image is compressed in the vehicle width direction to be displayed.

For example, the second determination unit <b>114</b> determines the compression ratio of the compression target area in the cutout area based on a table that associates the number of lanes detected by the first detection unit <b>112</b> with the compression ratio.

In principle, the larger the number of lanes is, the higher the compression ratio is, and the smaller the number of lanes is, the lower the compression ratio is. However, since the compression ratio may be too high if the number of lanes is too large, the second determination unit <b>114</b> may determine the upper limit of the compression ratio such that the compression ratio does not exceed the upper limit.

In the example of FIG. <b>6</b>, the second determination unit <b>114</b> determines the compression ratio corresponding to the number of lanes “3” detected by the first detection unit <b>112</b> as the compression ratios of the left area L and the right area R. The second determination unit <b>114</b> determines to compress the left area L and the right area R such that their dimensions in the vehicle width decrease to half, for example.

Returning to FIG. <b>3</b>, the description will be continued. The generation unit <b>115</b> generates a display image to be displayed on the display device by processing the captured image according to the processing conditions determined by the first determination unit <b>113</b> and the second determination unit <b>114</b>.

Specifically, the generation unit <b>115</b> first cuts out the cutout area C determined by the first determination unit <b>113</b> from the rear view image D. Next, the generation unit <b>115</b> performs compression processing on the left area L and the right area R of the cutout area C according to the compression ratio determined by the second determination unit <b>114</b>, and generates a display image to be displayed on the display device <b>25</b>. For example, the generation unit <b>115</b> performs the processing of compressing the left area L and the right area R such that their dimensions in the vehicle width decrease to half. The display image here is, for example, an image displayed based on the video signal SGr<b>2</b>.

In addition, the generation unit <b>115</b> performs image processing such as adjustment of color and contrast on the front view image received by the receiving unit <b>111</b>, and generates a display image. The display image here is, for example, an image displayed based on the video signal SGf<b>2</b>.

The display control unit <b>116</b> performs control to processes the captured image according to the processing conditions determined by the first determination unit <b>113</b> and the second determination unit <b>114</b>, and display the captured image on the display device. Specifically, the display control unit <b>116</b> performs control to display the display image generated by the generation unit <b>115</b> on the display device <b>25</b>. In addition, the display control unit <b>116</b> performs control to display the display image generated by the generation unit <b>115</b> on the display <b>45</b>.

FIG. <b>7</b> is an example of the display image displayed on the display device <b>25</b> according to the first embodiment. In the example of FIG. <b>7</b>, a display image W includes a left compression area LP, the essential display area E, and a right compression area RP. The essential display area E is displayed on the display device <b>25</b> at the same scale as that in the rear view image D by the display control unit <b>116</b>.

The left compression area LP is an area obtained by compressing the left area L of the cutout area C in FIG. <b>6</b> such that its dimension in the vehicle width decreases to half. The right compression area RP is an area obtained by compressing the right area R of the cutout area C in FIG. <b>6</b> such that its dimension in the vehicle width decreases to half. Note that the frames such as the black frame in FIG. <b>7</b> are drawn for convenience of description, and no frame is displayed in the actual display image W displayed on the display device <b>25</b>.

Although, in the above example, the second determination unit <b>114</b> determines to compress the compression target area of the cutout area C at the fixed compression ratio to decrease its dimension in the vehicle width direction to half, the compression ratio may vary depending on the position in the compression area. For example, the second determination unit <b>114</b> may determine the compression ratio such that the compression ratio of the compression area increases in a phased manner, as it goes outward from the center of the cutout area C.

FIG. <b>8</b> is an image view illustrating an example of the cutout area before compression in a case where the compression ratio is changed depending on the position in the compression area according to the first embodiment. In the example of FIG. <b>8</b>, the cutout area C includes a first left area L<b>1</b>, a second left area L<b>2</b>, the essential display area E, a first right area R<b>1</b>, and a second right area R<b>2</b>. The first detection unit <b>112</b> and the first determination unit <b>113</b> perform the same processing as that described with reference to FIGS. <b>5</b> and <b>6</b>.

The second determination unit <b>114</b> determines the compression ratio corresponding to the number of lanes “3” detected by the first detection unit <b>112</b>. For example, the second determination unit <b>114</b> determines to compress the first left area L<b>1</b> and the first right area R<b>1</b> such that their dimensions in the vehicle width direction decrease to half, and compress the second left area L<b>2</b> and the second right area R<b>2</b> such that their dimensions in the vehicle width direction decrease to quarter.

The generation unit <b>115</b> cuts out the cutout area C according to the determination of the first determination unit <b>113</b>. Then, the generation unit <b>115</b> performs the compression processing according to the compression ratios determined by the second determination unit <b>114</b> by compressing the first left area L<b>1</b> and the first right area R<b>1</b> in the cutout area C such that their dimensions in the vehicle width direction decrease to half and by compressing the second left area L<b>2</b> and the second right area R<b>2</b> such that their dimensions in the vehicle width direction decrease to quarter. The generation unit <b>115</b> then generates the display image W to be displayed on the display device <b>25</b>. The display control unit <b>116</b> displays the display image W generated by the generation unit <b>115</b> on the display device <b>25</b>.

FIG. <b>9</b> is an example of the display image displayed on the display device <b>25</b> according to the first embodiment. In the example of FIG. <b>9</b>, the display image W includes a first left compression area LP<b>1</b>, a second left compression area LP<b>2</b>, the essential display area E, a first right compression area RP<b>1</b>, and a second right compression area RP<b>2</b>. The essential display area E is displayed on the display device <b>25</b> at the same scale as that in the rear view image D by the display control unit <b>116</b>.

The first left compression area LP<b>1</b> is an area obtained by compressing the first left area L<b>1</b> of the cutout area C in FIG. <b>8</b> such that its dimension in the vehicle width direction decreases to half. The second left compression area LP<b>2</b> is an area obtained by compressing the second left area L<b>2</b> such that its dimension in the vehicle width direction decreases to quarter.

The first right compression area RP<b>1</b> is an area obtained by compressing the first right area R<b>1</b> such that its dimension in the vehicle width direction decreases to half. The second right compression area RP<b>2</b> is an area obtained by compressing the second right area R<b>2</b> such that its dimension in the vehicle width direction decreases to quarter. Note that the frames such as the black frame in FIG. <b>9</b> are drawn for convenience of description, and no frame is displayed in the actual display image W displayed on the display device <b>25</b>.

Thus, the second determination unit <b>114</b> determines the compression ratio such that the compression ratio in the vehicle width direction gradually increases from the inside of the host vehicle outward in the captured image, thereby, for example, making it possible to display an area closer to the host vehicle at a scale closer to that in the rear view image D, and an area farther away from the host vehicle at a higher compression ratio. Therefore, it is possible to display the display image W without reducing the visibility of the area having high importance for the user while reducing the area serving as the blind spot.

The second determination unit <b>114</b> may determine whether to keep the compression ratio fixed or change the compression ratio for each area according to the number of lanes. For example, the second determination unit <b>114</b> may keep the compression ratio fixed as illustrated in FIG. <b>7</b> when the number of lanes is three or less, and may change the compression ratio in a phased manner as illustrated in FIG. <b>9</b> when the number of lanes exceeds three.

Processing of Drive Recorder Unit of First Embodiment

Next, processing executed by the drive recorder unit <b>10</b> according to the first embodiment will be described. FIG. <b>10</b> is a flowchart illustrating an example of the processing executed by the drive recorder unit <b>10</b> according to the first embodiment.

First, the receiving unit <b>111</b> receives the rear view image generated by the rear camera <b>32</b> as the captured image (step S<b>1</b>).

Next, the first detection unit <b>112</b> detects the number of lanes based on the rear view image received by the receiving unit <b>111</b> (step S<b>2</b>).

Next, the first determination unit <b>113</b> determines the essential display area of the rear view image. Then, the first determination unit <b>113</b> determines the cutout area centered on the essential display area according to the number of lanes detected by the first detection unit <b>112</b> (step S<b>3</b>).

Next, the second determination unit <b>114</b> determines the compression ratio for the compression target area in the cutout area according to the number of lanes detected by the first detection unit <b>112</b> (step S<b>4</b>).

Next, the generation unit <b>115</b> cuts out the cutout area determined by the first determination unit <b>113</b> from the rear view image. Then, the generation unit <b>115</b> performs the processing of compressing the compression target area in the cutout area in the vehicle width direction according to the compression ratio determined by the second determination unit <b>114</b>, and generates a display screen to be displayed on the display device <b>25</b> (step S<b>5</b>).

Next, the display control unit <b>116</b> performs control to display the display image generated by the generation unit <b>115</b> on the display device <b>25</b> (step S<b>6</b>).

Next, the display control unit <b>116</b> determines whether or not to end displaying of the display image (step S<b>7</b>). For example, the display control unit <b>116</b> determines to end the displaying when a predetermined time has elapsed since a power source such as an engine of the vehicle <b>5</b> is stopped.

When the displaying of the display image is not ended (step S<b>7</b>: No), the processing proceeds to step S<b>1</b>. On the other hand, when ending the displaying of the display image (step S<b>7</b>: Yes), the display control unit <b>116</b> ends the processing.

Effects of Drive Recorder Unit According to First Embodiment

Next, effects of the drive recorder unit <b>10</b> according to the first embodiment will be described. The drive recorder unit <b>10</b> according to the present embodiment determines the processing conditions on the area other than the above-described essential display area in the captured image obtained by imaging the surroundings of the host vehicle according to the number of lanes indicating the number of one or more lanes including the lane on which the host vehicle travels.

More specifically, in the present embodiment, the second determination unit <b>114</b> determines the processing conditions so as to increase the compression ratio in proportion to the number of lanes. Therefore, the compression ratio decreases as the number of lanes is smaller. This can prevent a situation in which the captured image is compressed at a high compression ratio even when the number of lanes is small, which makes it difficult to view a vehicle laterally behind. That is, the drive recorder unit <b>10</b> according to the present embodiment can make it easier to view a vehicle or the like present laterally behind.

The “lane” includes a sidewalk. Therefore, the user can check the behavior of a pedestrian laterally behind by viewing the display device <b>25</b>.

Next, a drive recorder unit <b>10</b> according to the second embodiment will be described.

The drive recorder unit <b>10</b> according to the second embodiment is different from the drive recorder unit <b>10</b> according to the first embodiment in that the drive recorder unit <b>10</b> according to the second embodiment includes a second detection unit <b>117</b> as a functional unit. Hereinafter, the drive recorder unit <b>10</b> according to the second embodiment will be described with reference to FIGS. <b>11</b> to <b>17</b>. The same configurations and operations as those described in the first embodiment are denoted by the same reference numerals, and the description thereof will be omitted or simplified.

Functional Configuration of Drive Recorder Unit of Second Embodiment

A functional configuration of the drive recorder unit <b>10</b> according to the second embodiment will be described with reference to FIG. <b>11</b>. FIG. <b>11</b> is a functional block diagram illustrating an example of the functional configuration of the microcomputer <b>11</b> of the drive recorder unit <b>10</b> according to the second embodiment.

The drive recorder unit <b>10</b> according to the second embodiment further includes the second detection unit <b>117</b> in addition to the functional units included in the drive recorder unit <b>10</b> according to the first embodiment.

The second detection unit <b>117</b> detects the traveling position of the host vehicle. The second detection unit <b>117</b> is an example of the detection unit. Specifically, the second detection unit <b>117</b> detects a lane change line, a boundary between a roadway and a sidewalk, and the like from the rear view image received by the receiving unit <b>111</b>, and detects the traveling position of the host vehicle from a positional relationship between the detected lane change line, boundary, and the like in the rear view image.

Although, in the present embodiment, the second detection unit <b>117</b> detects the traveling position of the host vehicle from the captured image received by the receiving unit <b>111</b>, the second detection unit <b>117</b> may detect the traveling position of the host vehicle based on the reception result of a positioning signal. In addition, the second detection unit <b>117</b> may perform vehicle-to-roadside-infrastructure communication with a device installed on the road, and detect the traveling position of the host vehicle based on the communication result or the like. The communication result includes, for example, the communication speed and the signal strength.

The second detection unit <b>117</b> may also function as the above-described first detection unit <b>112</b>. Alternatively, the first detection unit <b>112</b> may also function as the second detection unit <b>117</b>.

FIG. <b>12</b> is a view illustrating an example of a rear view image of the host vehicle captured by the rear camera <b>32</b> according to the second embodiment. In the rear view image D illustrated in FIG. <b>12</b>, the vehicle A<b>1</b>, the vehicle A<b>2</b>, the lane B<b>1</b>, the lane B<b>2</b>, and the lane B<b>3</b> are drawn. In this example, the rear view image D is an image obtained by imaging the area behind the host vehicle traveling in the lane B<b>1</b> using the wide-angle rear camera <b>32</b>. The vehicle A<b>1</b> is traveling in the lane B<b>1</b> as the host vehicle does, and the vehicle A<b>2</b> is traveling in the lane B<b>3</b>.

In the example of FIG. <b>12</b>, the second detection unit <b>117</b> detects that the traveling position of the host vehicle is “the leftmost lane in the image” from the positional relationship between the lane B<b>1</b>, lane B<b>2</b>, and lane B<b>3</b> in the rear view image D. The leftmost lane in the image is the lane B<b>1</b>.

The first determination unit <b>113</b> determines the cutout area according to the number of lanes detected by the first detection unit <b>112</b> and the traveling position of the host vehicle detected by the second detection unit <b>117</b>.

Specifically, the first determination unit <b>113</b> performs the same processing as that of the first embodiment and determines the size of the cutout area. Next, the first determination unit <b>113</b> determines a cutout method for the cutout area according to the traveling position of the host vehicle detected by the second detection unit <b>117</b>.

For example, in a case where a lane or sidewalk is not present to the left of the host vehicle, the importance level of information on the left of the host vehicle decreases. In this case, the first determination unit <b>113</b> determines the cutout method such that the left end of the essential display area coincides with the left end of the cutout area.

FIG. <b>13</b> is an image view illustrating an example of processing of determining the cutout area according to the second embodiment. As illustrated in FIG. <b>13</b>, the first determination unit <b>113</b> determines the cutout method such that the left end of the essential display area E coincides with the left end of the cutout area C according to the fact that the traveling position of the host vehicle detected by the second detection unit <b>117</b> is the “leftmost lane in the image”.

In the example of FIG. <b>13</b>, the cutout area C includes the essential display area E and a compression target area O located to the right of the essential display area E in the image.

The second determination unit <b>114</b> determines processing conditions for the area other than the essential display area in the captured image according to the number of lanes detected by the first detection unit <b>112</b> and the traveling position of the host vehicle detected by the second detection unit <b>117</b>.

For example, the second determination unit <b>114</b> determines a compression method for the compression target area in the cutout area based on a table that associates the number of lanes detected by the first detection unit <b>112</b> and the traveling position detected by the second detection unit <b>117</b> with the compression method including the compression ratio.

For example, the traveling position is represented by a numerical value such as “1” for the leftmost lane or sidewalk that can be confirmed in the captured image, and “2” for its right lane. In addition, the compression method represents, for example, the compression ratio of the area to the left of the essential display area, and the compression ratio of the area to the right of the essential display area. In addition to this, the compression method may include the determination on whether or not to change the compression ratio in a phased manner.

For example, when the host vehicle is traveling in the leftmost lane, the second determination unit <b>114</b> increases the compression ratio of the area to the left of the essential display area and decreases the compression ratio of the right area. Note that the second determination unit <b>114</b> may determine the compression ratio for the right or the left as “not displayed”. The display device <b>25</b> does not display the area for which the compression ratio is determined as “non-displayed” by the second determination unit <b>114</b>. Determining the compression ratio of the area on the right or left as “not displayed” can be translated as compressing the area on the right or left at an infinite compression ratio.

In the example of FIG. <b>13</b>, the second determination unit <b>114</b> determines the compression method corresponding to the number of lanes “3” detected by the first detection unit <b>112</b> and the traveling position “1” detected by the second detection unit <b>117</b> as the compression method for the compression target area O. For example, the second determination unit <b>114</b> determines the left of the essential display area E as being non-displayed and the right of the essential display area E as being compressed such that its dimension in the vehicle width direction decreases to half. The traveling position “1” is the leftmost lane in the image as described above.

Since processing of the generation unit <b>115</b> and the display control unit <b>116</b> is the same as that of the first embodiment, description thereof is omitted. FIG. <b>14</b> is an example of the display image displayed on the display device <b>25</b> according to the second embodiment. In the example of FIG. <b>14</b>, the display image W includes the essential display area E and a compressed display area OP. The essential display area E is displayed on the display device <b>25</b> at the same scale as that in the rear view image D by the display control unit <b>116</b>.

The compressed display area OP is an area obtained by compressing the compression target area O on the right side of the cutout area C in FIG. <b>13</b> such that its dimension in the vehicle width direction decreases to half. Note that the frames such as the black frame in FIG. <b>13</b> are drawn for convenience of description, and no frame is displayed in the actual display image W displayed on the display device <b>25</b>.

Although, in the above example, the second determination unit <b>114</b> compresses the compression target area of the cutout area C at the fixed compression ratio to decrease its dimension in the vehicle width direction to half, the compression ratio may vary depending on the position in the compression area, similar to the first embodiment. For example, the second determination unit <b>114</b> may determine the compression ratio such that the compression ratio of the compression area increases in a phased manner from the center of the cutout area C outward.

FIG. <b>15</b> is an image view illustrating an example of the cutout area before compression in a case where the compression ratio is changed depending on the position in the compression area according to the second embodiment. In the example of FIG. <b>15</b>, the cutout area C includes the essential display area E, a first compression target area O<b>1</b>, and a second compression target area O<b>2</b>. The first detection unit <b>112</b>, the second detection unit <b>117</b>, and the first determination unit <b>113</b> perform the same processing as that described with reference to FIG. <b>13</b>.

The second determination unit <b>114</b> determines the compression method corresponding to the number of lanes “3” detected by the first detection unit <b>112</b> and the traveling position “1” detected by the second detection unit <b>117</b>. For example, the second determination unit <b>114</b> determines to compress the first compression target area O<b>1</b> such that its dimension in the vehicle width direction decrease to half and the second compression target area O<b>2</b> such that its dimension in the vehicle width direction decrease to quarter.

The generation unit <b>115</b> cuts out the cutout area C according to the determination of the first determination unit <b>113</b>. Then, the generation unit <b>115</b> performs the compression processing according to the compression method determined by the second determination unit <b>114</b> by compressing the first compression target area O<b>1</b> of the cutout area C such that its dimension in the vehicle width direction decrease to half and by compressing the second compression target area O<b>2</b> such that its dimension in the vehicle width direction decrease to quarter. The generation unit <b>115</b> then generates the display image W to be displayed on the display device <b>25</b>. The display control unit <b>116</b> displays the display image W generated by the generation unit <b>115</b> on the display device <b>25</b>.

FIG. <b>16</b> is an example of the display image displayed on the display device <b>25</b>. In the example of FIG. <b>16</b>, the display image W includes the essential display area E, a first compressed display area OP<b>1</b>, and a second compressed display area OP<b>2</b>. The essential display area E is displayed on the display device <b>25</b> at the same scale as that in the rear view image D by the display control unit <b>116</b>.

The first compressed display area OP<b>1</b> is an area obtained by compressing the first compression target area O<b>1</b> of the cutout area C in FIG. <b>15</b> such that its dimension in the vehicle width direction decrease to half. The second compressed display area OP<b>2</b> is an area obtained by compressing the second compression target area O<b>2</b> such that its dimension in the vehicle width direction decrease to quarter. Note that the frames such as the black frame in FIG. <b>15</b> are drawn for convenience of description, and no frame is displayed in the actual display image W displayed on the display device <b>25</b>.

The second determination unit <b>114</b> may determine the compression method for each area according to the number of lanes and the traveling position. For example, the second determination unit <b>114</b> may make the compression ratio uniform as illustrated in FIG. <b>14</b> when the number of lanes is three or less, and may change the compression ratio in a phased manner as illustrated in FIG. <b>16</b> when the number of lanes exceeds three.

In addition, the second determination unit <b>114</b> may change the compression method between the left and the right of the essential display area according to the traveling position. For example, in a case where the area to the right of the essential display area is larger than the area to the left of the essential display area in the cutout area, the second determination unit <b>114</b> may determine the compression ratio such that the compression ratio of the right area is higher than the compression ratio of the left area. For example, the second determination unit <b>114</b> may determine to compress the left area such that its dimension in the vehicle width direction decrease to half, compress a part closer to the essential display area in the right area such that its dimension in the vehicle width direction decrease to half, and compress another part farther away from the essential display area in the right area such that its dimension in the vehicle width direction decrease to quarter.

Processing of Drive Recorder Unit of Second Embodiment

Next, processing executed by the drive recorder unit <b>10</b> according to the second embodiment will be described. FIG. <b>17</b> is a flowchart illustrating an example of the processing executed by the drive recorder unit <b>10</b> according to the second embodiment.

First, the receiving unit <b>111</b> receives the rear view image generated by the rear camera <b>32</b> as the captured image (step S<b>11</b>).

Next, the first detection unit <b>112</b> detects the number of lanes based on the rear view image received by the receiving unit <b>111</b> (step S<b>12</b>).

Next, the second detection unit <b>117</b> detects the traveling position based on the rear view image received by the receiving unit <b>111</b> (step S<b>13</b>).

Next, the first determination unit <b>113</b> determines the essential display area of the rear view image. Then, the first determination unit <b>113</b> determines the size of the cutout area and the cutout method according to the number of lanes detected by the first detection unit <b>112</b> and the traveling position detected by the second detection unit <b>117</b> (step S<b>14</b>).

Next, the second determination unit <b>114</b> determines the compression method for the compression target area according to the number of lanes detected by the first detection unit <b>112</b> and the traveling position (step S<b>15</b>).

Next, the generation unit <b>115</b> cuts out the cutout area determined by the first determination unit <b>113</b> from the rear view image. Then, the generation unit <b>115</b> performs the processing of compressing the compression target area in the vehicle width direction according to the compression method determined by the second determination unit <b>114</b>, and generates a display screen to be displayed on the display device <b>25</b> (step S<b>16</b>).

Next, the display control unit <b>116</b> performs control to display the display image generated by the generation unit <b>115</b> on the display device <b>25</b> (step S<b>17</b>).

Next, the display control unit <b>116</b> determines whether or not to end displaying of the display image (step S<b>18</b>). For example, the display control unit <b>116</b> determines to end the displaying when a predetermined time has elapsed since a power source such as an engine of the vehicle <b>5</b> is stopped.

When the displaying of the display image is not ended (step S<b>18</b>: No), the processing proceeds to step S<b>11</b>. On the other hand, when ending the displaying of the display image (step S<b>18</b>: Yes), the display control unit <b>116</b> ends the processing.

Effects of Drive Recorder Unit According to Second Embodiment

Next, effects of the drive recorder unit <b>10</b> according to the second embodiment will be described. The drive recorder unit <b>10</b> according to the present embodiment determines processing conditions for the area other than the essential display area according to the traveling position of the host vehicle.

More specifically, in the present embodiment, the second determination unit <b>114</b> increases the compression ratio of the area to the left of the essential display area and decreases the compression ratio of the area to the right when the host vehicle is traveling in the leftmost lane. This is because when the host vehicle is traveling in the leftmost lane, no vehicle or the like is present to the left of the host vehicle, and thus it is less necessary to pay attention to the left of the host vehicle. On the other hand, since a vehicle or the like may be present to the right of the host vehicle, it is highly necessary to pay attention to the right.

Therefore, the drive recorder unit <b>10</b> according to the present embodiment can display only a portion having a high importance level with a low compression ratio, which allows makes it easier to view the portion. That is, it is possible to make it easier to view any vehicle or the like present laterally behind.

The above-described embodiments can be appropriately modified and implemented by changing a part of the configuration or function of the display control system <b>1</b>. Hereinafter, some modifications according to the above-described embodiments will be described as other embodiments. In the following description, points different from the above-described embodiments will be mainly described, and detailed description of points common to the contents already described will be omitted. In addition, the modifications described below may be implemented individually, or may be implemented in appropriate combination.

In the first embodiment and the second embodiment described above, the mode has been described in which the display control system <b>1</b> includes the drive recorder unit <b>10</b>, the display unit <b>20</b>, the front camera <b>31</b>, the rear camera <b>32</b>, and the display unit <b>40</b>. However, the display control system <b>1</b> may only include the display unit <b>20</b> and the rear camera <b>32</b>.

In this case, the ECU <b>21</b> of the display unit <b>20</b> loads the control program stored in the ROM of the ECU <b>21</b> in the RAM and causes the CPU to operate, thereby implementing each functional unit. The ECU <b>21</b> implements, for example, the receiving unit <b>111</b>, the first detection unit <b>112</b>, the first determination unit <b>113</b>, the second determination unit <b>114</b>, the generation unit <b>115</b>, and the display control unit <b>116</b> included in the microcomputer <b>11</b> as each functional unit.

In the first embodiment and the second embodiment described above, the mode has been described in which the rear view image subjected to compression processing is displayed on the display device <b>25</b>. However, the display control unit <b>116</b> may perform control to display the rear view image subjected to the compression processing on the display <b>45</b>. Alternatively, the display control unit <b>116</b> may perform control to display the rear view image subjected to the compression processing on a head-up display (HUD) or the like mounted on the vehicle <b>5</b>.

In the first embodiment and the second embodiment described above, the mode has been described in which only the rear view image is displayed on the display device <b>25</b>. However, an image in which the front view image is combined may be displayed on the display device <b>25</b>.

In the present modification, for example, the generation unit <b>115</b> generates a display image to be displayed on the display device <b>25</b> by combining the front left image ahead of the host vehicle cut out from the front view image such that the front left image lies to the left of the rear view image subjected to the compression processing, and the front right image ahead of the host vehicle cut out from the front view image such that the front right image lies to the right of the rear view image subjected to the compression processing.

The generation unit <b>115</b> may detect any pedestrian or a bicycle from the front view image, and generate the display image to be displayed on the display device <b>25</b> by combining the front view image with the rear view image only when any pedestrian or bicycle is present. Alternatively, the generation unit <b>115</b> may generate the display screen by setting only a roadway as the display target for the rear view image, setting only a sidewalk as the display target for the front view image, and combining the rear view image and the front view image.

The generation unit <b>115</b> generates the display image by combining the rear view image and the front view image, thereby allowing the user to obtain both rear and front information from one screen. This makes it easier for the user to view the surroundings of the host vehicle, thereby makes it possible to reduce the possibility of occurrence of an accident.

In the second embodiment described above, the mode has been described in which the second determination unit <b>114</b> determines the compression method for the captured image based on the number of lanes and the traveling position. However, in addition to these, the second determination unit <b>114</b> may determine the compression method based on the presence or absence of any vehicle or the like. Here, the vehicle includes a two-wheeled vehicle.

The second determination unit <b>114</b> of the present modification increases the compression ratio of an area where no other vehicle or the like is present in the captured image.

FIG. <b>18</b> is a view illustrating an example of a rear view image of a host vehicle according to a fourth modification. In the example of FIG. <b>18</b>, no vehicle is present in an area ON, and the vehicle A<b>2</b> is present in an area OE. In this case, the second determination unit <b>114</b> increases the compression ratio of the area ON, and sets the compression ratio of the area OE to be lower than that of the area ON.

FIG. <b>19</b> is an example of the display image to be displayed on the display device <b>25</b> according to the fourth modification. In the example of FIG. <b>19</b>, the display image W includes the essential display area E, a high compression area NP, and a low compression area EP. The essential display area E is displayed on the display device <b>25</b> at the same scale as that in the rear view image D by the display control unit <b>116</b>.

The high compression area NP is an area obtained by compressing the area ON of the cutout area C in FIG. <b>18</b> such that its dimension in the vehicle width direction decreases to quarter. The low compression area EP is an area obtained by compressing the area OE of the cutout area C in FIG. <b>18</b> such that its dimension in the vehicle width direction decreases to half. Note that the frames such as the black frame in FIG. <b>19</b> are drawn for convenience of description, and no frame is displayed in the actual display image W displayed on the display device <b>25</b>.

Thus, the second determination unit <b>114</b> sets the compression ratio to be higher for the area where no vehicle or the like is present and sets the compression ratio to be lower for the area where any vehicle or the like is present, thereby making it easier to view any object present laterally behind to which attention should be paid. Therefore, the drive recorder unit <b>10</b> of the present modification can make it easier to view any vehicle or the like present laterally behind.

The first determination unit <b>113</b> and the second determination unit <b>114</b> may determine the processing conditions for the captured image in conjunction with the operation of the direction indicator by the user.

When the user operates the direction indicator, the first determination unit <b>113</b> of the present modification determines the cutout area according to the user's operation. For example, the first determination unit <b>113</b> defines in advance the size of the cutout area and the cutout method for a case when the direction indicator indicates the left and the size of the cutout area and the cutout method for a case when the direction indicator indicates the right, and determines the cutout area according to the user's operation.

The second determination unit <b>114</b> determines the compression ratio of the compression target area in conjunction with the operation of the direction indicator by the user. For example, the second determination unit <b>114</b> determines the processing conditions such that the compression ratio of the area in the direction indicated by the direction indicator decreases with reference to the essential display area.

Here, a case will be considered where the user operates the direction indicator to indicate the right to change to the right lane in a state where the display image W in FIG. <b>7</b> is displayed on the display device <b>25</b>. In this case, the first determination unit <b>113</b> determines the size of the cutout area and the cutout method for a case when the direction indicator indicates the right. In this example, the first determination unit <b>113</b> determines the essential display area E and the right area R in FIG. <b>6</b> as the cutout area C.

Next, the second determination unit <b>114</b> decreases the compression ratio in the direction indicated by the direction indicator in the image. In this example, the second determination unit <b>114</b> decreases the compression ratio of the right area R in FIG. <b>6</b> and determines no compression.

FIG. <b>20</b> is a view illustrating an example of the display image to be displayed on the display device <b>25</b> according to the fifth modification. In the example of FIG. <b>20</b>, the display image W includes the essential display area E and the right area R. The essential display area E and the right area R are displayed on the display device <b>25</b> at the same scale as that in the rear view image D by the display control unit <b>116</b>. Note that the frames such as the black frame in FIG. <b>20</b> are drawn for convenience of description, and no frame is displayed in the actual display image W displayed on the display device <b>25</b>.

Thus, the second determination unit <b>114</b> decreases the compression ratio in the direction indicated by the direction indicator in the image, thereby, for example, making it easier for the user to view the right rear area when turning right or changing to the right lane. That is, according to the present modification, it is possible to make it easier to view any vehicle or the like present laterally behind.

The first determination unit <b>113</b> and the second determination unit <b>114</b> may determine the processing conditions for the captured image in conjunction with the operation of the steering wheel by the user.

When the user operates the steering wheel, the first determination unit <b>113</b> of the present modification determines the cutout area according to the user's operation. For example, the first determination unit <b>113</b> defines in advance the size of the cutout area and the cutout method for a case when the steering wheel is turned to the left and the size of the cutout area and the cutout method for a case when the steering wheel is turned to the right, and determines the cutout area according to the user's operation.

The determination on whether the steering wheel is turned to the left or the right is made based on, for example, whether the steering angle exceeds a threshold value.

The second determination unit <b>114</b> determines the compression ratio of the compression target area in conjunction with the operation of the steering wheel by the user. For example, the second determination unit <b>114</b> determines the processing conditions such that the compression ratio of the area in the direction to which the steering wheel is turned decreases with reference to the essential display area.

Here, a case will be considered where the user turns the steering wheel right to change to the right lane in a state where the display image W in FIG. <b>7</b> is displayed on the display device <b>25</b>. In this case, the first determination unit <b>113</b> determines the size of the cutout area and the cutout method for a case when the steering wheel is turned right. In this example, the first determination unit <b>113</b> determines the essential display area E and the right area R in FIG. <b>6</b> as the cutout area C.

Next, the second determination unit <b>114</b> decreases the compression ratio in the direction to which the steering wheel is turned in the image. In this example, the second determination unit <b>114</b> decreases the compression ratio of the right area R in FIG. <b>6</b> and determines no compression. Since the image of the display image is the same as that of the fifth modification, illustration and description thereof are omitted.

Thus, the second determination unit <b>114</b> decreases the compression ratio in the direction to which the steering wheel is turned in the image, thereby, for example, making it easier for the user to view the right rear area when turning right or changing to the right lane. That is, according to the present modification, it is possible to make it easier to view any vehicle or the like present laterally behind.

The first determination unit <b>113</b> and the second determination unit <b>114</b> may determine the processing conditions for the captured image in conjunction with the movement of the line of sight of the user.

When the user moves his/her line of sight, the first determination unit <b>113</b> of the present modification determines the cutout area according to the movement of the user's line of sight. For example, the first determination unit <b>113</b> defines in advance the size of the cutout area and the cutout method for a case when the user directs his/her line of sight to the left and the size of the cutout area and the cutout method for a case when the user directs his/her line of sight to the right, and determines the cutout area according to the movement of the user's line of sight.

The movement of the user's line of sight is detected by, for example, providing a camera or the like capable of imaging the user in the vehicle <b>5</b> and analyzing the image captured by the camera. The user is, for example, a driver.

The second determination unit <b>114</b> determines the compression ratio of the compression target area in conjunction with the movement of the user's line of sight. For example, the second determination unit <b>114</b> determines the processing conditions such that the compression ratio of the area in the direction to which the line of sight is directed decreases with reference to the essential display area.

Here, a case will be considered where the user directs his/her line of sight right to change to the right lane in a state where the display image W in FIG. <b>7</b> is displayed on the display device <b>25</b>. In this case, the first determination unit <b>113</b> determines the size of the cutout area and the cutout method for a case when the user directs his/her line of sight to the right. In this example, the first determination unit <b>113</b> determines the essential display area E and the right area R in FIG. <b>6</b> as the cutout area C.

Next, the second determination unit <b>114</b> decreases the compression ratio in the direction to which the user's line of sight is directed in the image. In this example, the second determination unit <b>114</b> decreases the compression ratio of the right area R in FIG. <b>6</b> and determines no compression. Since the image of the display image is the same as that of the fifth modification, illustration and description thereof are omitted.

Thus, the second determination unit <b>114</b> decreases the compression ratio in the direction to which the user's line of sight is directed in the image, thereby, for example, making it easier for the user to view the right rear area when turning right or changing to the right lane. That is, according to the present modification, it is possible to make it easier to view any vehicle or the like present laterally behind.

The first determination unit <b>113</b> and the second determination unit <b>114</b> may determine the processing conditions for the captured image in conjunction with a route guidance.

The first determination unit <b>113</b> of the present modification determines the cutout area according to the route guidance. For example, the first determination unit <b>113</b> defines in advance the size of the cutout area and the cutout method for a case when guiding to turn left and the size of the cutout area and the cutout method for a case when guiding to turn right, and determines the cutout area according to the route guidance.

The route guidance is to identify the current position and the traveling direction of the host vehicle, for example, by analyzing a positioning signal, and guide a route to a destination.

The second determination unit <b>114</b> determines the compression ratio of the compression target area according to the route guidance. For example, the second determination unit <b>114</b> determines the processing conditions such that the compression ratio of the area in the direction indicated by the route guide decreases with reference to the essential display area.

Here, a case will be considered where it is guided by the route guide to turn right in a state where the display image W of FIG. <b>7</b> is displayed on the display device <b>25</b>. In this case, the first determination unit <b>113</b> determines the size of the cutout area and the cutout method for a case when guiding to turn right. In this example, the first determination unit <b>113</b> determines the essential display area E and the right area R in FIG. <b>6</b> as the cutout area C.

Next, the second determination unit <b>114</b> decreases the compression ratio in the direction indicated by the route guide in the image. In this example, the second determination unit <b>114</b> decreases the compression ratio of the right area R in FIG. <b>6</b> and determines no compression. Since the image of the display image is the same as that of the fifth modification, illustration and description thereof are omitted.

Thus, the second determination unit <b>114</b> decreases the compression ratio in the direction indicated by the route guide in the image, thereby allowing the user to check the situation occurring laterally behind from a display image with less discomfort before operating the direction indicator. That is, according to the present modification, it is possible to make it easier to view any vehicle or the like present laterally behind.

The first determination unit <b>113</b> and the second determination unit <b>114</b> may determine the processing conditions for the captured image according to the traveling speed of the host vehicle.

In the present modification, when the speed of the host vehicle falls below a predefined threshold, the first determination unit <b>113</b> determines a predefined area in the captured image as the cutout area regardless of the number of lanes and the traveling position. When the traveling speed of the host vehicle falls below the predefined threshold, the second determination unit <b>114</b> sets the compression ratio of the compression target area to 0. The compression ratio of 0 means no compression.

In addition, the user may manually switch whether the first determination unit <b>113</b> and the second determination unit <b>114</b> perform the processing of determining the processing conditions for the captured image based on the number of lanes and the traveling position, or perform the above-described processing.

According to the drive recorder unit <b>10</b> according to the present modification, it is possible to display an uncompressed natural display image on the display device <b>25</b> in a scene where it is less necessary to pay attention to laterally behind, such as when the host vehicle is stopped. This makes it possible to reduce a scene where the user feels uncomfortable about the display image.

The first determination unit <b>113</b> and the second determination unit <b>114</b> may determine the processing conditions for the captured image according to the inter-vehicle distance.

In the present modification, when the inter-vehicle distance exceeds a predefined threshold, the first determination unit <b>113</b> determines a predefined area in the captured image as the cutout area regardless of the number of lanes and the traveling position. When the inter-vehicle distance exceeds the predefined threshold, the second determination unit <b>114</b> sets the compression ratio of the compression target area to 0. The compression ratio of 0 means no compression.

The inter-vehicle distance between the host vehicle and another vehicle is calculated by analyzing the rear view image D.

With the drive recorder unit <b>10</b> according to the present modification, it is possible to display an uncompressed natural display image on the display device <b>25</b> in a scene where it is less necessary to pay attention to laterally behind, such as when the inter-vehicle distance exceeds a certain distance. This makes it possible to reduce a scene where the user feels uncomfortable about the display image.

In the fourth modification described above, the mode has been described in which the second determination unit <b>114</b> decreases the compression ratio of the area where any vehicle or the like is present. However, the second determination unit <b>114</b> may decrease the compression ratio of the area for a lane where an entrance of a service area or the like is present. Here, the service area or the like includes, for example, a service area and a parking area.

The second determination unit <b>114</b> of the present modification decreases the compression ratio of the area for the lane where the entrance of the service area or the like is present in the captured image. The lane where the entrance of the service area or the like is present may be detected by analyzing the captured image, or may be detected from the reception result of a positioning signal or the like. In addition, the second determination unit <b>114</b> may perform the above processing only when a certain period of time has elapsed from the start of driving or the previous break.

Thus, decreasing the compression ratio of the area for the lane where the entrance of the service area or the like is present makes it easier for the user to check an area laterally behind when changing the lane to the lane where the entrance of the service area or the like is present to enter the service area or the like.

Although the embodiments of the present disclosure have been described above, the above-described embodiments are presented as examples, and are not intended to limit the scope of the invention. These novel embodiments can be implemented in various other forms, and various omissions, substitutions, and changes can be made without departing from the gist of the invention. These novel embodiments and modifications thereof are included in the scope and gist of the invention, and are included in the invention described in the claims and the equivalent scope thereof. Furthermore, the components of different embodiments and modifications may be appropriately combined.

Furthermore, the effects of each embodiment described herein are merely examples and are not limited, and other effects may be provided.

According to the present disclosure, it is possible to make it easier to view any vehicle or the like present laterally behind. Note that the effect described here is not necessarily limited, and may be any of the effects described in the description.

While certain embodiments have been described, these embodiments have been presented by way of example only, and are not intended to limit the scope of the inventions. Indeed, the novel methods and systems described herein may be embodied in a variety of other forms; furthermore, various omissions, substitutions and changes in the form of the methods and systems described herein may be made without departing from the spirit of the inventions. The accompanying claims and their equivalents are intended to cover such forms or modifications as would fall within the scope and spirit of the inventions.

## Claims

1. A display control device, comprising:
a memory that stores a program; and
a processor that is connected to the memory, wherein the processor performs first processing by executing the program, the first processing including:
detecting a number of lanes indicating one or more lanes, the lanes including a first lane on which a host vehicle travels;
determining a processing condition for an area, other than an essential display area including a predefined display area, from a captured image, obtained by imaging surroundings of the host vehicle, according to the number of lanes detected;
second processing of the captured image according to the processing condition determined; and
displaying the processed captured image on a display device,

wherein the determining of the processing condition includes determining a compression ratio in a vehicle width direction of the area other than the essential display area, and
the processor determines the compression ratio in the vehicle width direction of the area other than the essential display area such that the compression ratio is higher as the number of lanes detected is larger and is lower as the number of lanes detected is smaller.

2. The display control device according to claim 1,
wherein the lanes include a sidewalk on which a pedestrian walks and the first lane on which the host vehicle travels.

3. The display control device according to claim 1, wherein the first processing includes
detecting a traveling position of the host vehicle, and
determining the processing condition for the area in the captured image according to the number of lanes and the traveling position of the host vehicle detected.

4. The display control device according to claim 3,
wherein the first processing determines the processing condition such that the compression ratio in the vehicle width direction gradually increases from inside of the host vehicle outward in the captured image.

5. The display control device according to claim 3,
wherein the first processing determines the processing condition such that the compression ratio in the vehicle width direction increases in an area where any other vehicle is not present in the captured image.

6. The display control device according to claim 3,
wherein the first processing determines the processing condition, including the determining of the compression ratio in the vehicle width direction of the area, in conjunction with an operation of a direction indicator by a user.

7. The display control device according to claim 6,
wherein the first processing determines the processing condition such that the compression ratio in the vehicle width direction of a second area in a direction indicated by the direction indicator decreases with reference to the essential display area.

8. The display control device according to claim 3,
wherein the first processing determines the processing condition, including the determining of the compression ratio in the vehicle width direction of the area, in conjunction with an operation of a steering wheel by a user.

9. The display control device according to claim 8,
wherein the first processing determines the processing condition such that the compression ratio in the vehicle width direction of a second area in a direction in which the steering wheel is turned decreases with reference to the essential display area.

10. The display control device according to claim 3,
wherein the first processing determines the processing condition, including the determining of the compression ratio in the vehicle width direction of the area, in conjunction with movement of a line of sight of a user.

11. The display control device according to claim 10,
wherein the first processing determines the processing condition such that the compression ratio in the vehicle width direction of a second area in a direction in which the line of sight is directed decreases with reference to the essential display area.

12. The display control device according to claim 3,
wherein the first processing determines the processing condition, including the determining of the compression ratio in the vehicle width direction of the area, according to a route guide.

13. The display control device according to claim 12,
wherein the first processing determines the processing condition such that the compression ratio in the vehicle width direction of a second area in a direction indicated by the route guide decreases with reference to the essential display area.

14. The display control device according to claim 3,
wherein the first processing determines the processing condition such that the compression ratio in the vehicle width direction is 0 when a traveling speed of the host vehicle is below a predefined threshold.

15. A display control device, comprising:
a memory that stores a program; and
a processor that is connected to the memory, wherein the processor performs processing by executing the program, the processing including:
detecting a number of lanes indicating one or more lanes, the lanes including a first lane on which a host vehicle travels;
determining a processing condition for an area, other than an essential display area including a predefined display area, from a captured image, obtained by imaging surroundings of the host vehicle, according to the number of lanes detected;
processing the captured image according to the processing condition determined; and
displaying the processed captured image on a display device,

wherein the processing of the captured image includes
detecting a traveling position of the host vehicle,
determining the processing condition for the area other than the essential display area in the captured image according to the number of lanes and the traveling position of the host vehicle detected, and
determining the processing condition such that a display compression ratio in a vehicle width direction is 0 when an inter-vehicle distance exceeds a predefined threshold.

16. A display control method performed by a display control device, the display control method comprising:
detecting a number of lanes of one or more lanes, the lanes including a first lane on which a host vehicle travels;
determining, by a processor, a processing condition for an area, other than an essential display area including a predefined display area, from a captured image, obtained by imaging surroundings of the host vehicle, according to the number of lanes detected;
processing the captured image according to the processing condition determined; and
displaying the processed captured image on a display device,
wherein the determining of the processing condition by the processor includes determining a compression ratio in a vehicle width direction of the area other than the essential display area, and
the processor determines the compression ratio in the vehicle width direction of the area other than the essential display area such that the compression ratio is higher as the number of lanes detected is larger and is lower as the number of lanes detected is smaller.

