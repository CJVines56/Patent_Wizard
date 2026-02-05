# Memory repair device (Doc 12406745)

- Doc ID: 12406745
- Title: Memory repair device
- Filing Date: 20230510
- Classification: G11C 29/4401
- Authors: Jun Soo Kwack; Yong Sup Lee

## Abstract

A memory repair device for detecting a fault cell in a memory and replacing it with a redundancy cell using a serial interface method is provided. The memory repair device include a repair information control block and at least one memory block including at least one memory. The repair information control block is configured to perform a built-in self-test (BIST) for each memory block, and when a fault cell is detected according to the BIST, receive and store repair information about the fault cell information. The memory block replaced the fault cell with a redundancy cell according to repair information loaded by the repair information control block at the time of operation of the memory. Data is transmitted and received between the repair information control block and the memory block using a serial interface.

## Description

This application claims the benefit under 35 U.S.C. § 119 of Korean Patent Application No. 10-2022-0136525 filed on Oct. 21, 2022, in the Korean Intellectual Property Office, the entire disclosure of which is incorporated herein by reference for all purposes.

The present description relates to a memory repair device for detecting a fault cell in a memory using a serial interface method and replacing it with a redundancy cell.

Recently, the degree of integration of circuits on a single chip is rapidly increasing due to the development of design and process technologies along with demands for high performance, high functionality, and miniaturization of the system. Therefore, it may be necessary to integrate more devices in a limited area, and in particular, to further improve the function of a chip, an integrated circuit such as a System-On-Chip (SOC) is designed to be equipped with multiple memories.

Yield improvement of an integrated circuit may vary depending on how effectively a memory is repaired. A method of repairing a memory detects a fault cell and replaces the fault cell with a redundancy cell such that the memory and the integrated circuit including the same operate normally. When the memory is repaired, it may be possible to continuously use the memory having the fault cell as well as the integrated circuit equipped with the memory without discarding it as a defective product.

In this way, detecting and replacing a fault cell with a redundancy cell to ensure normal operation of the memory may be an important factor in improving the yield and quality of an integrated circuit designing and manufacturing an integrated circuit having a memory.

This Summary is provided to introduce a selection of concepts in a simplified form that are further described below in the Detailed Description. This Summary is neither intended to identify key features or essential features of the claimed subject matter, nor is it intended to be used as an aid in determining the scope of the claimed subject matter.

In a general aspect, a memory repair device including: a repair information control block and a memory block with at least one memory. The repair information control block controls a Built-in Self-Test (BIST) to be performed for each memory block, and if a fault cell is confirmed as a result of the BIST, the repair information control block receives and stores repair information related to the fault cell in a repair information storage block. The memory block performs memory repair by replacing the fault cell with a redundancy cell according to repair information loaded by the repair information control block at the time of operation of the memory.

Data between the repair information control block and the memory block may be transmitted and received in a serial interface method through an interface conversion circuit.

The repair information control block may include: a BIST control circuit for generating a fault cell detection command for BIST of the memory block; a first interface conversion circuit for converting the fault cell detection command into serial data; and a repair information alignment circuit for aligning repair information transmitted from the memory block such that the repair information is stored in a predetermined location of the repair information storage block.

The memory block may include: a second interface conversion circuit for generating a BIST start flag when the serial data is converted into a fault cell detection command; a BIST circuit for testing whether there is a fault cell in a memory according to the fault cell detection command; and a Built-in Redundancy Analysis (BIRA) circuit for detecting and transmitting, if there is a fault cell as a result of the test, repair information related to the fault cell to the repair information control block.

The repair information may include address information of the fault cell and index information indicating the memory block where the fault cell is located.

The BIST circuit may include: a pattern generation circuit for generating pattern information suitable for a size of the memory and storing data and addresses in the memory; and a pattern confirmation circuit for confirming whether there is a fault cell based on pattern information of the data provided by the memory.

The pattern generation circuit may generate the pattern information if the BIST start flag is received from the second interface conversion circuit.

The BIRA circuit may include: a fault cell address detection circuit for detecting a fault cell address; and a fault cell address conversion circuit for receiving a user address and remapping a fault cell address to a redundancy cell address to be transmitted to the memory when repair process is performed by the repair information control block.

The repair information storage block may be located inside the memory block or outside the memory block.

The interface conversion circuit may include a first interface conversion circuit and a second interface conversion circuit for transmitting serial data between the repair information control block and the memory block. The first interface conversion circuit may transmit serial data by a clock signal generated by a clock generation unit. The second interface conversion circuit may transmit serial data by a clock signal provided by the clock generation unit of the first interface conversion circuit.

In another general aspect, a memory repair device includes: a repair information control block; and memory blocks connected to the repair information control block through a serial interface. The repair information control block loads previously stored repair information to transmit the loaded repair information to the corresponding memory block. The memory block remaps a fault cell address to a redundancy cell address based on the repair information to repair a memory.

The repair information control block may access to only memory blocks need repair such that a memory repair is performed.

The memory block may perform a repair process if repair information loaded by the repair information control block is transmitted at a time of operation of the memory.

The repair information control block may load the previously stored repair information from a repair information storage block.

The repair information storage block may be located inside the memory block or outside the memory block.

In another general aspect, a memory repair device includes: memory blocks; and a memory control unit for performing grouping with memory blocks based on a same size of memory cells. The memory block includes: memory devices having memory cells of a same size; a single BIST circuit for detecting a fault cell of the memory devices; BIRA circuits provided in each of the memory devices; and a serial interface circuit for serial communication with the memory control unit.

The memory control unit may perform a Built-in Self-Test (BIST) on memory devices of various sizes provided in each of the memory blocks at one time and repairs a memory device with a fault cell.

The memory control unit may generate pattern information and address corresponding to a size of a memory cell.

The memory control unit, during a period in which a BIST function of a memory block with memory cells of a relatively large size is performed, may turn off a BIST function of a memory block having memory cells of a relatively small size so that a clock signal is not generated.

FIG. <b>1</b> illustrates a block diagram of a memory repair device according to the conventional art.

FIG. <b>2</b> illustrates an example diagram in which memory blocks access to a repair information storage unit to store repair information in a memory repair device according to the conventional art.

FIG. <b>3</b> illustrates a block diagram of a memory repair device according to various aspects of the present disclosure.

FIG. <b>4</b> illustrates an internal block diagram of the first interface conversion circuit and the second interface conversion circuit of FIG. <b>3</b> according to various aspects of the present disclosure.

FIG. <b>5</b> illustrates a block diagram of a memory repair device according to a various aspects of the present disclosure.

FIGS. <b>6</b> and <b>7</b> illustrate diagrams for comparison between a repair processing method according to the conventional art and a repair processing method according to various aspects of the present disclosure.

FIG. <b>8</b>A illustrates a diagram of a state before grouping memory cells of different sizes in a memory repair device according to the conventional art.

FIG. <b>8</b>B illustrates a block diagram of memory cells grouped by same size in a memory repair device according to various aspects of the present disclosure.

FIG. <b>9</b> illustrates a timing diagram for a Built-in Self test (BIST) operation of memory blocks having memory cells grouped by size according to various aspects of the present disclosure.

The following detailed description is provided to assist the reader in gaining a comprehensive understanding of the methods, apparatuses, and/or systems described herein. However, various changes, modifications, and equivalents of the methods, apparatuses, and/or systems described herein will be apparent after an understanding of the disclosure of this application. For example, the sequences of operations described herein are merely examples, and are not limited to those set forth herein, but may be changed as will be apparent after an understanding of the disclosure of this application, with the exception of operations necessarily occurring in a certain order. Also, descriptions of features that are known after an understanding of the disclosure of this application may be omitted for increased clarity and conciseness, noting that omissions of features and their descriptions are also not intended to be admissions of their general knowledge.

Although terms such as “first,” “second,” and “third” may be used herein to describe various members, components, regions, layers, or sections, these members, components, regions, layers, or sections are not to be limited by these terms. Rather, these terms are only used to distinguish one member, component, region, layer, or section from another member, component, region, layer, or section.

The terms “comprises,” “includes,” and “has” specify the presence of stated features, numbers, operations, members, elements, and/or combinations thereof, but do not preclude the presence or addition of one or more other features, numbers, operations, members, elements, and/or combinations thereof.

Spatially relative terms such as “above,” “upper,” “below,” and “lower” may be used herein for ease of description to describe one element's relationship to another element as shown in the figures. Such spatially relative terms are intended to encompass different orientations of the device in use or operation in addition to the orientation depicted in the figures. For example, if the device in the figures is turned over, an element described as being “above” or “upper” relative to another element will then be “below” or “lower” relative to the other element. Thus, the term “above” encompasses both the above and below orientations depending on the spatial orientation of the device. The device may also be oriented in other ways (for example, rotated 90 degrees or at other orientations), and the spatially relative terms used herein are to be interpreted accordingly.

The terms indicating a part such as “part” or portion” used herein to mean that the component may represent a device that may include a specific function, a software that may include a specific function, or a combination of device and software that may include a specific function, but it is not necessarily limited to the function expressed. This is only provided to help a more general understanding of one or more examples herein, and various modifications and variations are possible from these descriptions by those of ordinary skill in the art to which the one or more examples pertains.

In addition, it should be noted that all electrical signals used herein are examples, and when an inverter or the like is additionally provided in the circuit in accordance with one or more embodiments, the signs of all electrical signals to be described below may be reversed. Accordingly, the scope of the embodiments is not limited to the direction or polarity of the signal.

The features of the examples described herein may be combined in various ways as will be apparent after an understanding of the disclosure of this application. Further, although the examples described herein have a variety of configurations, other configurations are possible as will be apparent after an understanding of the disclosure of this application.

A detailed description is given below, with attached drawings. The features of the examples described herein may be combined in various ways as will be apparent after an understanding of the disclosure of this application. Further, although the examples described herein have a variety of configurations, other configurations are possible as will be apparent after an understanding of the disclosure of this application.

In some aspects, the detecting and repairing a fault cell may be required to improve the quality of the memory. In general, Built-in Self-Test (BIST) is configured to detect and repair a fault cell, and a BIST will first be described with reference to a repair method according to the conventional art.

The present description is provided to suggest a memory repair device that may improve the yield and quality of integrated circuits.

The present description is provided also to suggest a memory repair device in which the number of routers for transmitting repair information is reduced as compared to the conventional art.

FIG. <b>1</b> illustrates a block diagram of a memory repair device according to the conventional art.

Referring to FIG. <b>1</b>, a memory repair device <b>1</b> includes a repair information provision blocks <b>2</b>-<b>2</b><i>n</i>, a repair information control block <b>3</b>, and memory blocks <b>4</b>-<b>4</b><i>n. </i>

The repair information provision blocks <b>2</b>-<b>2</b><i>n </i>may include a BIST circuit for obtaining repair information related to a fault cell of a memory. The repair information includes address information of the fault cell to be replaced with a redundancy cell and an index indicating a memory block.

The repair information control block <b>3</b> includes repair information storage units <b>31</b>-<b>31</b><i>n </i>that store repair information transmitted by the repair information provision block <b>2</b> and loads the repair information stored in the repair information storage units <b>31</b>-<b>31</b><i>n </i>during initial operation of the memory and then performs the function of transmitting repair information to a memory block <b>4</b>. The repair information storage units <b>31</b>-<b>31</b><i>n </i>may include flash memories or one-time programmable (OTP) memories.

The memory blocks <b>4</b>-<b>4</b><i>n </i>may include repair processing units <b>41</b>-<b>41</b><i>n </i>that replace a fault cell with a redundancy cell using repair information transmitted by the repair information control block <b>3</b>. In some aspects, the repair processing units <b>41</b>-<b>41</b><i>n </i>perform a repair process overall.

However, as illustrated, the repair information is transmitted between the repair information control block <b>3</b> and memory blocks <b>4</b>-<b>4</b><i>n </i>in parallel of a pin-to-pin structure. In some cases, when a chip is designed to increase the number of memory blocks <b>4</b>-<b>4</b><i>n </i>and the size of a memory, the number of routings required for information transmission (e.g., electrical conductors) to be transmitted increases accordingly. For example, in the case of an integrated circuit with 10 memories, 4 redundancy cells, and 10 bits of repair address, if repair is performed using the pin-to-pin method, this was possible with approximately 800 routings. When repair information is transmitted in parallel, it is difficult to perform repair and not easy to apply in practice.

FIG. <b>2</b> illustrates a diagram in which memory blocks access a repair information storage unit to store repair information in a memory repair device according to the conventional art.

As illustrated in FIG. <b>2</b>, repair information that is generated in each memory is stored in one repair information storage unit <b>31</b>. Thus, when memory repair is performed, a plurality of memory blocks <b>4</b> simultaneously access to the repair information storage unit <b>31</b> storing repair information. Congestion issue may occur and may cause repair information to be transmitted incorrectly.

In this way, in the repair device according to the conventional art, since the repair information is transmitted in parallel through a transmission path connected by a pin-to-pin type hard wire, the number of routings cannot be reduced and there high possibility of errors in transmission of the repair information due to congestion.

In some aspects, a serial interface may prevent congestion issues and improve operation of the memory repair device. When using the serial interface, the number of routings may be reduced and the congestion issue may be also solved.

FIG. <b>3</b> illustrates a block diagram of a memory repair device according to various aspects of the present disclosure.

A memory repair device <b>100</b> in FIG. <b>3</b> according to a first aspect of the present disclosure includes a repair information storage block <b>110</b>, a repair information control block <b>120</b>, and a memory block <b>130</b>. The blocks <b>110</b>, <b>120</b>, <b>130</b> communicate with each other through a serial interface.

The repair information control block <b>120</b> performs a BIST on the memory block <b>130</b> and controls the repair process when there is a memory to be repaired.

In one illustrative aspect, the repair information control block <b>120</b> is configured to include a BIST control circuit <b>1210</b> that generates a fault cell detection command for BIST in the memory block <b>130</b>, a first interface conversion circuit <b>1220</b> that encodes and converts the fault cell detection command into serial data to be transmitted to the memory block <b>130</b>, and a repair information alignment circuit <b>1230</b> that aligns repair information transmitted from the memory block <b>130</b> to be stored in a corresponding storage location of the repair information storage block <b>110</b>.

The memory block <b>130</b> performs a BIST according to the control operation of the repair information control block <b>120</b> and transmits the result of the performance to the repair information control block <b>120</b>. The memory block <b>130</b> may be configured to include a second interface conversion circuit <b>1340</b>, a memory <b>1320</b>, a BIST circuit <b>1310</b>, a Built-in Redundancy Analysis (BIRA) circuit <b>1330</b>, etc.

The second interface conversion circuit <b>1340</b> decodes serial data transmitted by the first interface conversion circuit <b>1220</b> and converts the serial data back into a fault cell detection command. At this time, the second interface conversion circuit <b>1340</b> transmits a BIST start flag to a pattern generation circuit <b>1312</b> of the BIST circuit <b>1310</b>.

The BIST circuit <b>1310</b> includes a pattern generation circuit <b>1312</b> and a pattern confirmation circuit <b>1314</b> and tests whether there is a fault cell in a memory based on the fault cell detection command. After receiving the BIST start flag, the pattern generation circuit <b>1312</b> generates patterns suitable for the size of the memory (e.g., various combinations of binary numbers using algorithms such as modified algorithmic test sequence++(MATS++) and March C−) and inputs data and addresses corresponding to the patterns into the memory <b>1320</b>. The pattern confirmation circuit <b>1314</b> confirms whether there is a fault cell based on a pattern of data output by the memory <b>1320</b>.

The BIRA circuit <b>1330</b> includes a fault cell address detection circuit <b>1332</b> and a fault cell address conversion circuit <b>1334</b>. The fault cell address detection circuit <b>1332</b> detects a fault cell based on an Error_Flag transmitted by the pattern confirmation circuit <b>1314</b> and transmits information related to the detected fault cell to the second interface conversion circuit <b>1340</b> and the fault cell address conversion circuit <b>1334</b>. Herein, the information related to the detected fault cell becomes repair information. The repair information includes address information that identifies a fault cell and index information indicating a memory block in which the fault cell is located. In addition, the repair information may include Bit Fail information including bit information related to a fault cell. The fault cell address conversion circuit <b>1334</b> receives a user address(User ADD), remaps a fault cell address to a redundancy cell address, and transmit the remapped the redundancy cell address to the memory.

The repair information storage block <b>110</b> stores repair information transmitted by the repair information alignment circuit <b>1230</b>.

FIG. <b>4</b> illustrates an internal block diagram of the first interface conversion circuit and the second interface conversion circuit of FIG. <b>3</b> according to various aspects of the present disclosure.

As illustrated in FIG. <b>4</b>, a first interface conversion circuit <b>1220</b> includes a first serializer converter <b>1240</b> and a second serial-parallel converter <b>1250</b>, and a second interface conversion circuit <b>1340</b> includes a first serial-parallel converter <b>1350</b> and a second serializer converter <b>1360</b>. Herein, since the first serializer converter <b>1240</b> and the second serializer converter <b>1360</b> have a similar configuration and the first serial-parallel converter <b>1350</b> and the second serial-parallel converter <b>1250</b> have a similar configuration, the configuration of one serializer converter and one serial-parallel converter will be described.

The first serializer converter <b>1240</b> includes a first data mapping unit <b>1241</b>, a clock generation unit <b>1242</b>, a first converter <b>1243</b>, and a line driver <b>1244</b>. The first data mapping unit <b>1241</b> maps a fault cell detection command for starting BIST, the first converter <b>1243</b> converts the fault cell detection command into serial data, and the line driver <b>1244</b> transmits the transmitted serial data. The transmission of serial data is performed according to a clock signal generated by the clock generation unit <b>1242</b>.

The first serial-parallel converter <b>1350</b> includes a second data mapping unit <b>1351</b>, a second converter <b>1352</b>, and a line receiver <b>1353</b>. The line receiver <b>1353</b> communicates with the line driver <b>1244</b> of the first serializer converter <b>1240</b> to receive serial data, the second converter <b>1352</b> converts the serial data into a fault cell detection command, and the second data mapping unit <b>1351</b> transmits the fault cell detection command to each memory.

The first serializer converter <b>1240</b> of the first interface conversion circuit <b>1220</b> is included the clock generation unit <b>1242</b> while the second serializer converter <b>1360</b> of the second interface conversion circuit <b>1340</b> is not included a clock generation unit. This is because the second serializer converter <b>1360</b> transmits serial data according to a clock signal generated by the clock generation unit <b>1242</b> of the first serializer converter <b>1240</b>.

A repair method of the memory repair device according to one example of the present disclosure is as follows.

In some aspects, the repair method begins by detecting a fault cell by performing BIST tests on a plurality of memory blocks <b>130</b>.

In some cases, to detect a fault cell, a BIST control circuit <b>1210</b> of the repair information control block <b>120</b> generates a fault cell detection command to perform a BIST on each memory <b>1320</b> provided in each memory block <b>130</b>.

A fault cell detection command generated by the BIST control circuit <b>1210</b> is transmitted to each memory block <b>130</b>. At this time, the fault cell detection command is transmitted through a serial interface designed to reduce the number of routings as compared to a parallel method. In detail, the first interface conversion circuit <b>1220</b> converts a fault cell detection command into serial data and transmits the serial data to the second interface conversion circuit <b>1340</b> provided in each memory block <b>130</b>. Then, the second interface conversion circuit <b>1340</b> decodes the serial data and converts the serial data into a fault cell detection command to test whether there is a fault cell in each memory <b>1320</b>.

When the second interface conversion circuit <b>1340</b> converts serial data into a fault cell detection command, a BIST start flag information is generated, and the BIST start flag is transmitted to a pattern generation circuit <b>1312</b>. Then, the pattern generation circuit <b>1312</b> generates pattern information suitable for each memory size, such as MATS++, March C−, and inputs data and addresses corresponding to the pattern information into the memory <b>1320</b>. After that, a pattern confirmation circuit <b>1314</b> confirms whether data RDATA outputted from the memory <b>1320</b> is identical to the inputted data WDATA. The pattern confirmation circuit <b>1314</b> detects whether there is a fault cell in the memory <b>1320</b> based on differences in the inputted data WDATA and the data RDATA read from the memory <b>1320</b>.

As a result of the confirmation by the pattern confirmation circuit <b>1314</b>, if there is no fault cell, no information is generated and tests are repeatedly performed. In some case, if there is a fault cell at an address in the memory <b>1320</b>, the pattern confirmation circuit <b>1314</b> transmits Error_Flag information including address information to a fault cell address detection circuit <b>1332</b> of a BIRA circuit <b>1330</b>.

The fault cell address detection circuit <b>1332</b> receives the Error_Flag, confirms that there is a fault cell in the corresponding memory <b>1320</b>, and detects repair information based on the Error_Flag. As described above, repair information includes repair address information and an index indicating a memory block. The detected repair information is transmitted to the second interface conversion circuit <b>1340</b> and a fault cell address conversion circuit <b>1334</b>. Then, the second interface conversion circuit <b>1340</b> converts the repair information into serial data and transmits the data (e.g., serialized repair information) to the first interface conversion circuit <b>1220</b>, and the first interface conversion circuit <b>1220</b> decodes and transmits the serial data to a repair information alignment circuit <b>1230</b>. The repair information alignment circuit <b>1230</b> stores the decoded repair information in a predetermined location of the repair information storage block <b>110</b>. The repair information transmitted to the fault cell address conversion circuit <b>1334</b> is used when the fault cell is replaced with a redundancy cell by receiving a user address(User ADD) at the time when the memory <b>1320</b> operates.

Through this process, a repair information control block <b>120</b> performs a test for each memory block <b>130</b>, and, if there is a fault cell, repair information transmitted by a corresponding memory block may be stored in a repair information storage block <b>110</b>. Therefore, a plurality of repair information is stored in the repair information storage block <b>110</b>.

Aspects of a repair process using the repair information stored in the repair information storage block <b>110</b> will be described next.

The repair process of replacing a fault cell with a redundancy cell uses repair information loaded by the repair information control block <b>120</b>. At this time, the repair information control block <b>120</b> knows a memory block with a fault cell and a fault cell address information of the corresponding memory. According to the conventional art, when a memory block is reset after operation of detecting a fault cell, operation of finding an address information of the fault cell again. On the contrary, the repair information control block <b>120</b> according to the present disclosure does not require operation of finding the address information of the fault cell to be repaired. In one aspect, the repair information control block <b>120</b> recognizes the address information of a memory to be repaired even though the memory block is reset after the operation of detecting the fault cell.

The repair process for a fault cell starts with loading repair information from the repair information storage block <b>110</b> by the repair information control block <b>120</b> at the time when the memory operates. At this time, when repair information is loaded, the repair information stored in the repair information storage block <b>110</b> is sequentially loaded and thus memory blocks with fault cell information are sequentially accessed.

The repair information loaded by the repair information control block <b>120</b> is transmitted to a corresponding memory block through the first interface conversion circuit <b>1220</b> and the second interface conversion circuit <b>1340</b>. In some cases, to repair the fault cell, the memory block <b>130</b> remaps a fault cell address to a redundancy cell address based on the repair information and the user address(User ADD).

In this way, according to examples of the present disclosure, repair may be performed by loading only repair information stored in the repair information storage block <b>110</b> and transmitting it to the memory <b>1320</b>.

FIG. <b>5</b> illustrates a block diagram of a memory repair device <b>200</b> according to various aspects of the present disclosure.

Comparing the configuration according to the aspect in FIG. <b>5</b> with the configuration of FIG. <b>3</b> according to the first example, there may be some differences when it comes to the configuration in which a repair information storage circuit <b>2335</b> is provided inside a BIRA circuit <b>2330</b> and the configuration in which a repair information alignment circuit is removed from a repair information control block <b>220</b>. All other configurations are the same as those of the example of FIG. <b>3</b>. Accordingly, description of other configurations will be omitted.

The repair process according to the aspect illustrated in FIG. <b>5</b> is as follows.

First, a fault cell is detected. For example, to detect a fault cell, a BIST control circuit <b>2210</b> of the repair information control block <b>220</b> generates a fault cell detection command to perform a BIST on a memory <b>2320</b> provided in each memory block <b>230</b>.

The fault cell detection command generated by the BIST control circuit <b>2210</b> is encoded into serial data through a first interface conversion circuit <b>2220</b> and serially transmitted to a second interface conversion circuit <b>2340</b> of each memory block <b>230</b>.

Each memory block <b>230</b> receives the serial data (e.g., encoded fault cell detection command), decodes the serial data into the fault cell detection command using the second interface conversion circuit <b>2340</b>, and determines whether there is a fault cell in each memory <b>2320</b> according to the decoded fault cell detection command.

The test process is performed in the similar way as described above with reference to FIG. <b>3</b>. For example, when a pattern generation circuit <b>2312</b> receives a BIST start flag, the pattern generation circuit <b>2312</b> generates patterns, such as MATS++, March C−, suitable for the size of a memory and inputs data and addresses into the memory <b>2320</b>. A pattern confirmation circuit <b>2314</b> confirms whether the pattern is correctly generated based on the pattern information provided from the memory <b>2320</b>. Then pattern confirmation circuit <b>2314</b> determines whether there is a fault cell in the memory <b>2320</b>.

As a result of confirmation of the pattern confirmation circuit <b>2314</b>, if there is no fault cell, no information is generated. In some cases, if there a fault cell in an address of the memory <b>2320</b>, the pattern confirmation circuit <b>2314</b> transmits an Error_Flag information including an address information to a fault cell address detection circuit <b>2332</b> of the BIRA circuit <b>2330</b>. Then, the fault cell address detection circuit <b>2332</b> confirms that there is a fault cell in the memory <b>2320</b> and detects repair information based on the Error_Flag information. The detected repair information is transmitted to the repair information control block <b>220</b> through the second interface conversion circuit <b>2340</b> and the first interface conversion circuit <b>2220</b> and is also transmitted and stored in the repair information storage circuit <b>2335</b>.

In such state, when the memory <b>2320</b> operates, the repair information control block <b>220</b> loads the repair information from the repair information storage circuit <b>2335</b> provided in the memory block <b>230</b>. A repair is performed when the fault cell address conversion circuit <b>2334</b> remaps a fault cell address to a redundancy cell address based on the loaded repair information and the user address(User ADD).

In some aspects, the repair information control block <b>220</b> sequentially accesses only memory blocks to be repaired such that the repair is performed.

FIGS. <b>6</b> and <b>7</b> illustrate diagrams for comparison between a repair processing method according to the conventional art and a repair processing method according to various aspects of the present disclosure.

FIG. <b>6</b> illustrates a repair processing method according to a conventional structure, and it may be seen that a repair information control block <b>3</b> and each of memory blocks <b>4</b>-<b>4</b><i>n </i>are connected in parallel of a Pin-to-Pin structure. In other words, the number of routings is equal to the number of the memory blocks <b>4</b>-<b>4</b><i>n</i>. Thus, when a chip design is requested to increase the number and size of memories, the amount of information to be transmitted increases and the number of routings inevitably increases. An increase in the number of routings may limit reducing the design area of an integrated circuit.

In addition, in the conventional structure, since a plurality of memory blocks <b>4</b>-<b>4</b><i>n </i>simultaneously access the repair information control block <b>3</b>, the design of the integrated circuit must also account for congestion issues.

FIG. <b>7</b> illustrates a diagram of a repair processing method according to the present disclosure, and one repair information control block <b>120</b> and a plurality of memory blocks <b>130</b>-<b>130</b><i>n </i>are connected through a serial interface to perform repair. As compared to FIG. <b>6</b>, the number of routings may be significantly reduced, so congestion issue may be fundamentally prevented and increase space for layout of various components on the integrated circuit.

FIG. <b>8</b>A illustrates a diagram of a state before grouping memory cells of different sizes in a memory repair device according to the conventional art.

When detecting and repairing a fault cell in a memory block having memory cells of the same size in an integrated circuit, one BIST circuit and the same number of BIRA circuits as the number of memory cells are required. However, when there are memory cells having different sizes in one memory block, multiple BIST circuits may be included in the integrated circuit because the pattern lengths and address lengths of the memory cells are different from each other.

As illustrated in FIG. <b>8</b>A, when each of memory blocks <b>310</b>, <b>320</b> has memory cells of different sizes, a single BIST circuit is unable detect and repair fault cells of the memory cells. For example, as described above, pattern lengths and the number of addresses of memory cells are different.

In detail, referring to the memory block <b>310</b> of FIG. <b>8</b>A, the sizes of memory cells included in memory devices <b>310</b><i>a</i>, <b>310</b><i>c</i>, <b>310</b><i>d </i>are different from the size of memory cell included in the memory device <b>310</b><i>b</i>. Also, the sizes of memory cells included inside the memory devices <b>320</b><i>a</i>, <b>320</b><i>b </i>are different from each other. When the memory block is configured in this way, it is not easy for a single BIST circuit to detect and repair fault cells of memory cells. Therefore, as illustrated in FIG. <b>8</b>A, a BIST circuit and a serial interface circuit are required for each memory device.

FIG. <b>8</b>B illustrates a block diagram of memory cells grouped by same size in a memory repair device according to various aspects of of the present disclosure. According to examples of the present disclosure, when a memory block has memory cells of different sizes, memory cells of the same size may be grouped into a memory block to detect and repair a fault cell.

FIG. <b>8</b>B illustrates a state in which a memory control unit <b>5</b> inspects the sizes of memory cells and grouping memory devices with memory cells of the same size into a first memory block <b>310</b> and a second memory block <b>320</b>. The first memory block <b>310</b> is grouped with memory devices having memory cells of the same size (e.g., size A), that is, <b>310</b><i>a</i>, <b>310</b><i>b</i>, <b>310</b><i>c</i>, and <b>310</b><i>d</i>, and the second memory block <b>320</b> is grouped with memory devices having memory cells of the same size (e.g., size B), that is, <b>320</b><i>a </i>and <b>320</b><i>b</i>. In such configuration, since pattern lengths and the number of addresses of memory cells are the same in respective memory blocks <b>310</b>, <b>320</b>, each memory block <b>310</b>, <b>320</b> may include a single BIST circuit, a single serial interface circuit for communicating with a repair information control block, and N number of BIRA circuits corresponding to the number of memory cells.

In some aspects, if memory cells of the same size are grouped to form a memory block, a test time of the detecting a fault cell may be reduced.

FIG. <b>9</b> illustrates a timing diagram for a BIST operation of memory blocks having memory cells grouped by size according to various aspects of the present disclosure.

In FIG. <b>8</b>B, it is assumed that the size of a memory cell of a first memory block <b>310</b> is greater than the size of a memory cell of a second memory block <b>320</b> (e.g., size A>size B).

In this case, referring to FIG. <b>9</b>, label (a) illustrates when a BIST Enable signal changes from low level to high level, label (b) illustrates that the first BIST circuit of the first memory block <b>310</b> generates a high level of A BIST Enable signal, label (d) illustrates that a second BIST circuit of the second memory block <b>320</b> also generates a high-level of B BIST Enable signal (S).

While the A BIST Enable signal and the B BIST Enable signal maintain a high level, the first BIST circuit generates A BIST Clock signal at label (c) and, at label (e), and the second BIST circuit generates B BIST Clock signal at label (e), respectively. At this time, due to the difference in memory size, the first BIST circuit in the first memory block <b>310</b> has a larger memory cell operates for a longer time, as illustrated in label (c). Therefore, as illustrated in label (e) of FIG. <b>9</b>, there is a period CL in which the second BIST circuit of the second memory block <b>320</b> does not operate.

According to one or more examples of the present disclosure, during the period CL, the memory control unit <b>5</b> may prevent the clock signal and pattern signal of the second BIST circuit from being generated, thereby reducing current consumption. If there are memory cells of different sizes for each memory block, a BIST circuit is required for each size of the memory cell, and the BIST circuit must be activated continuously, resulting in continuous current loss.

According to the present disclosure, the number of routings required for repair information transmission may be reduced by allowing data to be transmitted between a repair information control block and a memory block in a serial interface. The serial interface may prevent a congestion issue from occurring during the repair process and prevent miscommunication of information, thereby improving the yield and quality of the integrated circuit.

According to the present disclosure, by grouping memory devices including memory cells of the same size for each memory block, the number of circuit elements required for each memory block may be reduced, thereby reducing space of the chip area and also reducing the test time for detecting a fault cell. In addition, it may be possible to reduce the current consumption generated during the test period since all memory blocks are not tested and memory blocks with small-sized memory cells do not need to be tested while other memory blocks with large-sized memory cells are being tested.

As described above, since a memory is repaired using a serial interface according to examples of the present disclosure, the number of routings may be reduced compared to the conventional art, and it may be seen that BIST time may be shortened by grouping memory cells by the same size for each memory block to perform repair.

## Claims

1. A memory repair device comprising:
at least one memory block including at least one memory;
a memory control unit configured to inspect sizes of the at least one memory and group the at least one memory of a same size into a corresponding memory block; and
a repair information control block configured to:
perform a Built-in Self-Test (BIST) for each memory block of the at least one memory block, and
when a fault cell is detected as a result of the BIST, receive and store repair information related to the fault cell in a repair information storage block,
wherein the memory block is configured to repair the fault cell with a redundancy cell according to the repair information when the memory block loads the repair information during operation of the at least one memory.

2. The memory repair device of claim 1, wherein, data is transmitted and received between the repair information control block and the memory block using a serial interface associated with an interface conversion circuit.

3. The memory repair device of claim 2, wherein the interface conversion circuit comprises a first interface conversion circuit and a second interface conversion circuit configured to transmit serial data between the repair information control block and the memory block,
wherein the first interface conversion circuit transmits the serial data based on a clock signal generated by a clock generation unit, and
wherein the second interface conversion circuit transmits the serial data based on the clock signal provided by the clock generation unit of the first interface conversion circuit.

4. The memory repair device of claim 1, wherein the repair information control block comprises:
a BIST control circuit configured to generate a fault cell detection command for BIST of the memory block;
a first interface conversion circuit configured to converts the fault cell detection command into serial data; and
a repair information alignment circuit configured to align the repair information transmitted from the memory block such that the repair information is stored in a predetermined location of the repair information storage block.

5. The memory repair device of claim 1, wherein the memory block comprises:
a second interface conversion circuit configured to generate a BIST start flag when serial data is converted into a fault cell detection command;
a BIST circuit configured to detect whether the fault cell according to the fault cell detection command; and
a Built-in Redundancy Analysis (BIRA) circuit configured to detect and transmit the repair information related to the fault cell to the repair information control block based on detecting the fault cell.

6. The memory repair device of claim 5, wherein the BIST circuit includes:
a pattern generation circuit configured to generate pattern information suitable for a size of the memory and storing data and addresses in the memory; and
a pattern confirmation circuit configured to detect the fault cell based on the pattern information of the data provided by the memory.

7. The memory repair device of claim 6, wherein the pattern generation circuit is configured to generate the pattern information if the BIST start flag is received from the second interface conversion circuit.

8. The memory repair device of claim 5, wherein the BIRA circuit comprises:
a fault cell address detection circuit configured to detect a fault cell address; and
a fault cell address conversion circuit configured to receive a user address and remap the fault cell address to a redundancy cell address to be transmitted to the memory when a repair process is performed by the repair information control block.

9. The memory repair device of claim 1, wherein the repair information comprises address information of the fault cell and index information indicating the memory block where the fault cell is located.

10. The memory repair device of claim 1, wherein the repair information storage block is located inside the memory block or outside the memory block.

11. A memory repair device comprising:
a repair information control block;
memory blocks including memory cells connected to the repair information control block through a serial interface; and
a memory control unit configured to inspect sizes of the memory cells and group the memory cells of a same size into a corresponding memory block,
wherein the repair information control block is configured to load and transmit previously stored repair information to the memory blocks, and
wherein the memory block repairs a memory by remapping a fault cell address to a redundancy cell address based on the repair information.

12. The memory repair device of claim 11, wherein the repair information control block only accesses the memory block that is determined to include at least one fault cell to repair the memory.

13. The memory repair device of claim 11, wherein the memory block is configured to perform a repair process if the repair information loaded by the repair information control block is transmitted at a time of operation of the memory.

14. The memory repair device of claim 11, wherein the repair information control block loads the repair information from a repair information storage block.

15. The memory repair device of claim 14, wherein the repair information storage block is located inside the memory block or outside the memory block.

16. A memory repair device comprising:
memory blocks; and
a memory control unit configured to group the memory blocks having memory cells of the same size into a corresponding memory block,
wherein each memory block of the memory blocks comprises:
memory devices having memory cells of a same size;
a single Built-in Self-Test (BIST) circuit configured to detect a fault cell of the memory devices;
BIRA circuits, a BIRA-Buit-in Redundancy Analysis (BIRA) circuit provided in each of the memory devices; and
a serial interface circuit configured to communicate with the memory control unit.

17. The memory repair device of claim 16, wherein the memory control unit is configured to:
perform a Built-in Self-Test on the memory devices of various sizes provided in each of the memory blocks at one time; and
repair a memory device including the fault cell.

18. The memory repair device of claim 16, wherein the memory control unit generates pattern information and address corresponding to a size of a memory cell.

19. The memory repair device of claim 16, wherein the memory control unit is configured to, during a period in which a BIST function of a memory block with memory cells of a first size is performed, turn off a BIST function of a memory block with memory cells of a second size so that a clock signal is not generated, wherein the first size is greater than the second size.

