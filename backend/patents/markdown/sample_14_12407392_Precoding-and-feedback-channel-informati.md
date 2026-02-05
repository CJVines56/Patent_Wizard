# Precoding and feedback channel information in wireless communication system (Doc 12407392)

- Doc ID: 12407392
- Title: Precoding and feedback channel information in wireless communication system
- Filing Date: 20240415
- Classification: H04B 7/065
- Authors: Jianjun Li; Kyoungmin Park

## Abstract

The present invention relates to precoding and feedback channel information in wireless communication system. A method includes receiving a first Precoding Matrix Index (PMI) and a second PMI from a terminal; mapping one or two codewords into layers; precoding symbols mapped into the layers using a first precoding matrix derived from the first PMI and a second precoding matrix derived from the second PMI; and transmitting the precoded symbols to the terminal, wherein the reception of the first PMI is less frequent than the reception of the second PMI.

## Description

This application is a continuation of U.S. patent application Ser. No. 17/170,808, filed on Feb. 8, 2021, which is a continuation of U.S. patent application Ser. No. 16/819,625, filed on Mar. 16, 2020, now issued as U.S. Pat. No. 10,917,157, which is a continuation of U.S. patent application Ser. No. 16/203,319, filed on Nov. 28, 2018, which a continuation of U.S. patent application Ser. No. 15/814,605, filed on Nov. 17, 2017, now issued as U.S. Pat. No. 10,153,821, which a continuation of U.S. patent application Ser. No. 15/131,725, filed on Apr. 18, 2016, now issued as U.S. Pat. No. 9,825,686, which a continuation of U.S. patent application Ser. No. 13/500,288, filed on Apr. 4, 2012, now issued as U.S. Pat. No. 9,319,252, which is the National Stage Entry of International Application PCT/KR2009/005705, filed on Oct. 6, 2009, all of which are incorporated herein by reference for all purposes as if fully set forth herein.

The present invention relates to precoding and feedback channel information in wireless communication system.

There are a number of multi-antenna transmission schemes or transmission such as transit diversity, closed-loop spatial multiplexing or open-loop spatial multiplexing. Closed-loop MIMO (CL-MIMO) relies on more extensive feedback from the mobile terminal.

In accordance with an aspect, there is provided a method or a system, comprising: mapping one or two codewords to the layers; precoding a mapped set of symbols using a precoding matrix derived from at least two downlink channel information where one of them is for rank adaptation and power allocation and the other of them is for the precoding without rank adaptation and power allocation and transmitting a signal that comprises the precoded set of symbols.

In accordance with another aspect, there is provided a method or a system for feedbacking channel information for the mobile terminal, the method comprising: estimating a downlink channel from the received signal; selecting one matrix for rank adaptation plus power allocation and the other matrix for the precoding without rank adaptation and power allocation based on the estimated channel state information and feedbacking the PMI (Precoding Matrix Index) of the selected matrix for rank adaptation and power allocation by long term and the PMI of the selected matrix for the original precoding by short term to the base station.

FIG. <b>1</b> is the block diagram of the wireless communication system using closed-loop spatial multiplexing according to one embodiment.

FIG. <b>2</b> is the diagram of the precoder according to the other embodiment.

FIG. <b>3</b> is the flowchart of the CL-MIMO according to other embodiment.

It will be appreciated that for simplicity and clarity of illustration, elements illustrated in the drawings have not necessarily been drawn to scale. For example, the dimensions of some of the elements are exaggerated relative to other elements for purposes of promoting and improving clarity and understanding. Further, where considered appropriate, reference numerals have been repeated among the drawings to represent corresponding or analogous elements.

Hereinafter, embodiments of the present invention will be described in detail with reference to the attached drawings.

There are a number of multi-antenna transmission schemes or transmission such as transit diversity, closed-loop spatial multiplexing or open-loop spatial multiplexing. Closed-loop MIMO (CL-MIMO) relies on more extensive feedback from the mobile terminal.

A unitary precoding is employed for Single User CL-MIMO (SU CL-MIMO), and unitary codebooks for different antenna configuration are defined. In LTE advance, it can be non-unitary also. Moreover, rank adaptation is also considered in LTE to enhance the performance.

However, in LTE, there is no power allocation among different layers if the rank is larger than 1. It is well known that unitary precoding with water filling power allocation is the optimal solution for CL-MIMO. So the original CL-MIMO in LTE is not optimal.

In this exemplary embodiment, a multi level precoding scheme is proposed for CL-MIMO. In the proposed scheme, we consider the use of two level precoding. The first level precoding is for rank adaptation and power allocation, and the second one is for unitary precoding. With the proposed scheme, we can get optimal solution for CL-MIMO. So it can increase the CL-MIMO performance. By harmonizing rank adaptation and power allocation, we can use fewer coding bits to show the same information so that it can reduce the overhead. Moreover, by using multilevel precoding, we can separately feedback the PMI for each level. The first level PMI is feedbacked less frequently than the second one. So the feedback overhead is further reduced.

FIG. <b>1</b> is the block diagram of the wireless communication system using closed-loop spatial multiplexing according to one embodiment.

Referring to FIG. <b>1</b>, the communication system may be any type of wireless communication system, including but not limited to a MIMO system, SDMA system, CDMA system, OFDMA system, OFDM system, etc. In the communication system, the wireless communication system using closed-loop spatial multiplexing according to one embodiment comprises a transmitter <b>10</b> and a receiver <b>20</b>. The transmitter <b>10</b> may act as a base station, while the receiver <b>20</b> may act as a subscriber station, which can be virtually any type of wireless one-way or two-way communication device such as a cellular telephone, wireless equipped computer system, and wireless personal digital assistant. Of course, the receiver/subscriber station <b>20</b> can also transmits signals which are received by the transmitter/base station <b>10</b>. The signals communicated between the transmitter <b>10</b> and the receive <b>20</b> can include voice, data, electronic mail, video, and other data, voice, and video signals.

In operation, the transmitter <b>10</b> transmits a signal data stream through one or more antennas and over a channel to a receiver <b>20</b>, which combines the received signal from one or more receiver antennas to reconstruct the transmitted data. To transmit the signal, the transmitter <b>10</b> prepares a transmission signal represented by the vector for the signal.

The transmitter <b>10</b> comprises a layer mapper <b>30</b> and a precoder <b>40</b>.

The layer mapper <b>30</b> of the transmitter <b>10</b> maps one or two codewords, corresponding to one or two transports, to the layers N<sub>L </sub>which may range from a minimum of one layer up to a maximum number of layers equal to the number of antenna ports. In case of multi-antenna transmission, there can be up to two transport blocks of dynamic size for each TTI (Transmission Time Interval), where each transport block corresponds to one codeword in case of downlink spatial multiplexing. In other words, the block of modulation symbols (one block per each transport block) refers to as a codeword. If there is only one codeword, we call it single codeword (SCW). Otherwise, we call it multiple codeword (MCW).

After layer mapping by the layer mapper <b>30</b>, a set of N<sub>L </sub>symbols (one symbol from each layer) is linearly combined and mapped to the N<sub>A </sub>antenna port by the precoder <b>40</b>. This combining/mapping can be described by means of a precoding matrix P of size N<sub>L</sub>×N<sub>A</sub>.

In various example embodiments, the precoding matrix P is implemented with the matrix P=WD, where D is a first level matrix for rank adaptation and power allocation, and W is a second level matrix for the original precoding. It can be unitary or non-unitary without power allocation information.

The precoder <b>40</b> has its own codebook, which is accessed to obtain a transmission profile and/or precoding information to be used to process the input data signal to make best use of the existing channel conditions for individual receiver stations. In addition, the receive <b>20</b> includes the same codebook for use in efficiently transferring information in either the feedback or feedforward channel, as described herein below.

In various embodiments, the codebook is constructed as a composite product codebook from separable sections, where the codebook index may be used to access the different sections of the codebook. For example, one or more predetermined bits from the codebook index are allocated for accessing the first level matrix, while a second set of predetermined bits from the second level index is allocated to indicate the values for the second level matrix.

In various embodiments, instead of having a single codebook at each of the transmitter <b>10</b> and the receiver <b>20</b>, separate codebooks can be stored so that there is, for example, a codebook for the first level precoding matrix W, a codebook for the second level matrix D. In such a case, separate indices may be generated wherein each index points to a codeword in its corresponding codebook, and each of these indices may be transmitted over a feedback channel to the transmitter, so that the transmitter uses these indices to access the corresponding codewords from the corresponding codebooks and determine a transmission profile or precoding information.

FIG. <b>2</b> is the diagram of the precoder according to the other embodiment.

Referring to FIG. <b>2</b>, after layer mapping by the layer mapper <b>30</b>, a set of N<sub>L </sub>symbols (one symbol from each layer) is linearly combined and mapped to the N<sub>A </sub>antenna port by the precoder <b>40</b>.

The precoder <b>40</b> comprises two level precoders <b>42</b> and <b>44</b> to optimize the performance. The first level precoder <b>42</b> is for rank adaptation and power allocation. The second level one <b>44</b> is for the original precoding.

In various example embodiments, the first precoder <b>42</b> may precode a set of symbols from the layer mapper <b>30</b> by means of a precoding matrix D of size N<sub>L</sub>×N<sub>L</sub>. The second precoder <b>44</b> may also precode a set of symbols from the first precoder <b>42</b> by means of a precoding matrix W of size N<sub>L</sub>×N<sub>A</sub>. The precoding matrix D is a first level matrix for rank adaptation and power allocation, and the precoding matrix W is a second level matrix for the original precoding. As a result, the first and the second precoder <b>42</b> and <b>44</b> precode a set of symbols by means of the matrix P=WD.

To assist the base station in selecting a suitable precoding matrix for transmission by the transmitter (<b>10</b>), the receiver/mobile terminal <b>20</b> may report channel information such as a recommended number of layers (expressed as a Rank Indication, RI) or a recommended precoding matrix (Precoding Matrix Index, PMI) corresponding to that number of layers, depending on estimates of the downlink channel conditions.

Referring to FIGS. <b>1</b> and <b>2</b> again, the receiver <b>20</b> comprises a channel estimator <b>50</b> and a post-decoder <b>60</b>.

The channel estimator <b>50</b> of the receiver <b>20</b> estimates the downlink channel condition. The channel estimator <b>50</b> feedbacks at least one of RI and PMI to the transmitter <b>10</b>. The channel estimator <b>50</b> may perform many kinds of codebook based PMI feedback.

The receiver <b>20</b> estimates the channel by the channel estimator <b>50</b>. Based on the estimated channel information, then the receiver <b>20</b> selects the precoding matrix for each level from the corresponding codebooks, which can make the system have the highest sum rate. Once the precoding matrix for each level is decided, the receiver/mobile terminal <b>20</b> separately feedback the PMIs of both level to the transmitter <b>10</b>.

There is codebook based PMI feedback where the receiver/mobile terminal <b>20</b> feedbacks the precoding matrix index (PMI) of the favorite matrix in the codebook to the transmitter/base station <b>10</b> to support CL-MIMO (closed MIMO) operation in wireless communication system.

The feedback frequency of the receiver <b>20</b> is different for different level precoding. The first level precoding is for rank adaptation and power allocation, which is decided by the channel amplitude. The second level precoding is for the original precoding, which is mainly decided by the phase. Since the phase changes much faster than the amplitude, the change of PMI feedback for the first level precoding is also much slower than the change of PMI feedback for the second one. So the first level precoding is by long term feedback and the second one is by short term feedback. So multi level precoding can reduce the feedback overhead.

The transmitter <b>10</b> receives PMI feedback for the first level precoding by long term and PMI feedback for the second level precoding by short term. The transmitter <b>10</b> precodes the set of symbols by means of the precoding matrix P=WD based on the two feedback PMIs as shown in FIG. <b>1</b>, where D is the first level matrix for rank adaptation and power allocation, and W is the second level matrix for the original precoding. In the other embodiment as shown in FIG. <b>2</b>, the transmitter <b>10</b> precodes the set of data symbols by means of the two level precoders <b>42</b> and <b>44</b> based on the two feedback PMIs. For example, the first precoder <b>42</b> and the second precoder <b>44</b> in turn precodes the set of data symbols by means of each of matrices W or D based on the long and the short-term feedback PMIs.

Then the transmitter <b>10</b> transmits the precoded data symbols by different antennas.

The receiver <b>20</b> recovers the original data symbols by post-decoder <b>60</b> with the previous feedback precoding matrices combination. The post-decoder <b>60</b> processes the received signal and decodes the precoded symbols.

FIG. <b>3</b> is the flowchart of the CL-MIMO according to other embodiment.

Referring to FIGS. <b>1</b> to <b>3</b>, in the multilevel precoding CL-MIMO, the receiver <b>20</b> estimates the channel S<b>10</b>. Based on the estimated channel information, the receiver <b>20</b> computes the sum rate for all the possible combinations of the two level precoding matrices from the codebooks.

The receiver <b>20</b> picks one matrix from the first level codebook and picks another one from the second level codebook. Then the receiver <b>20</b> computes the sum rate of the system when combining these two matrices together for precoding. The receiver <b>20</b> computes the sum rate for all the possible combinations and selects the one which has the highest sum rate. In other words, the receiver <b>20</b> selects the precoding matrix for each level from the corresponding codebooks S<b>20</b>, which has the highest sum rate among all the possible combinations.

Once the precoding matrix for each level is decided, the receiver <b>20</b> feedbacks the PMIs of the matrix in the best combination to the transmitter <b>10</b>.

In multiple level precoding, the first level is for rank adaptation and power allocation, which is decided by the channel amplitude. The second level precoding is the original, which is mainly decided by the phase. Since the phase changes much faster than the amplitude, the change PMI feedback of for the first level precoding is also much slower than the second one.

In multilevel precoding, the first level is for rank adaptation and power allocation. So the codebook is not unitary. By harmonizing rank adaptation and power allocation, we can use fewer coding bits to show the same information so that it can reduce the overhead.

    
    
        1) For rank adaptation information in the codebook, the identity matrix with some 1 element replaced by zeros can be used. It can also indicate the information that equal power allocation is used. So that we reduce the coding bits
        2) For power allocation, it attach to each rank. The total power is not changed. The diagonal matrix is used in the codebook for power allocation.
        3) For the exact value for power allocation, we can drive them from transmit adaptive antennas (TxAA) codebook, or by simulation to get the optimized value.

Table 1 gives an example of the first level codebook for 2×2 CL MIMO.1.

TABLE 1





Codebook




index
codebook
Meaning







0



 
  [
  
   
    
     1
    
    
     0
    
   
   
    
     0
    
    
     0
    
   
  
  ]
 



Rank 1


 


1



 
  
   1
   
    2
   
  
  [
  
   
    
     1
    
    
     0
    
   
   
    
     0
    
    
     1
    
   
  
  ]
 



Rank 2 Equal power allocation


 


2



 
  [
  
   
    
     
      2
      
       5
      
     
    
    
     0
    
   
   
    
     0
    
    
     
      1
      
       5
      
     
    
   
  
  ]
 



Rank 2 None Equal power allocation


 


3



 
  [
  
   
    
     
      1
      
       5
      
     
    
    
     0
    
   
   
    
     0
    
    
     
      2
      
       5
      
     
    
   
  
  ]
 



Rank 2 None Equal power allocation

Referring to the table 1, each of codebook indices has each of codebooks. Each of codebooks means rank adaptation and power allocation. For example, the codebook of codebook index “0” is

[
   
    
     
      1
     
     
      0
     
    
    
     
      0
     
     
      0
     
    
   
   ]
  
  ,
 


<br/>
which means rank 1. The codebook of codebook index “1” is

1
    
     2
    
   
   [
   
    
     
      1
     
     
      0
     
    
    
     
      0
     
     
      1
     
    
   
   ]
  
  ,
 


<br/>
which means rank 2 and equal power allocation. The codebook of codebook index “2” is

[
   
    
     
      
       2
       
        5
       
      
     
     
      0
     
    
    
     
      0
     
     
      
       1
       
        5
       
      
     
    
   
   ]
  
  ,
 


<br/>
which means rank 2 and unequal power allocation. The codebook of codebook index “3” is

[
   
    
     
      
       1
       
        5
       
      
     
     
      0
     
    
    
     
      0
     
     
      
       2
       
        5
       
      
     
    
   
   ]
  
  ,
 


<br/>
which means rank 2 and unequal power allocation.

So the receiver <b>20</b> does not need feedback the PMIs for both levels all the time. In every feedback, the receiver <b>20</b> feedbacks the PMI for the second level precoding. For every several feedbacks, the receiver <b>20</b> feedbacks the PMI for the first level precoding.

Before the PMI feedbacks, the receiver <b>20</b> checks whether the PMI of the first level need to be feedbacked S<b>30</b> because the feedback of the first level precoding is less frequent than the feedback of the second one. If the first level precoding is needed, the receiver <b>20</b> feedbacks the PMIs for both level precodings to the transmitter separately S<b>40</b>. Otherwise, it only feedbacks the second level precoding S<b>50</b>.

At the transmitter <b>10</b>, it precodes the data symbols by using the two level precoder based on the feedback PMIs, and then transmit the precoded data symbols by different antennas.

At the receiver <b>20</b>, it recovers the original data symbols by post-decoder <b>60</b> with the previous feedback precoding matrices combination.

In the original LTE CL-MIMO, there is no power allocation among different layers. It is well known that unitary precoding with water filling power allocation is the optimal solution for CL-MIMO. So the original CL-MIMO in LTE is not optimal.

In this exemplary embodiment, a multi level precoding scheme is proposed for CL-MIMO. In the proposed scheme, we consider use two level precoding. The first level precoding is for rank adaptation and power allocation, and the second one is for original precoding. With the proposed scheme, we can get optimal solution for CL-MIMO. So it can increase the CL-MIMO performance.

By harmonizing rank adaptation and power allocation, we can use fewer coding bits to show the same information so that it can reduce the overhead.

By using multilevel precoding, we can separately feedback the PMI for each level. Since the change in the feedback PMI for the first level precoding is much slower than that of the second one, the feedback frequency is different for different level precoding. We feed back the first level PMI less frequently than the second one. So multilevel precoding can reduce the feedback.

The methods and systems as shown and described herein may be implemented in software stored on a computer-readable medium and executed as a computer program on a general purpose or special purpose computer to perform certain tasks. For a hardware implementation, the elements used to perform various signal processing steps at the transmitter (e.g., coding and modulating the data, precoding the modulated signals, preconditioning the precoded signals, and so on) and/or at the receiver (e.g., recovering the transmitted signals, demodulating and decoding the recovered signals, and so on) may be implemented within one or more application specific integrated circuits (ASICs), digital signal processors (DSPs), digital signal processing devices (DSPDs), programmable logic devices (PLDs), field programmable gate arrays (FPGAs), processors, controllers, micro-controllers, microprocessors, other electronic units designed to perform the functions described herein, or a combination thereof. In addition or in the alternative, a software implementation may be used, whereby some or all of the signal processing steps at each of the transmitter and receiver may be implemented with modules (e.g., procedures, functions, and so on) that perform the functions described herein. It will be appreciated that the separation of functionality into modules is for illustrative purposes, and alternative embodiments may merge the functionality of multiple software modules into a single module or may impose an alternate decomposition of functionality of modules. In any software implementation, the software code may be executed by a processor or controller, with the code and any underlying or processed data being stored in any machine-readable or computer-readable storage medium, such as an on-board or external memory unit.

Although the described exemplary embodiments disclosed herein are directed to various MIMO precoding systems and methods for using same, the present invention is not necessarily limited to the example embodiments illustrate herein. For example, various embodiments of a MIMO precoding system and design methodology disclosed herein may be implemented in connection with various proprietary or wireless communication standards, such as IEEE 802.16e, 3GPP-LTE, DVB and other multi-user MIMO systems. Thus, the particular embodiments disclosed above are illustrative only and should not be taken as limitations upon the present invention, as the invention may be modified and practiced in different but equivalent manners apparent to those skilled in the art having the benefit of the teachings herein. Accordingly, the foregoing description is not intended to limit the invention to the particular form set forth, but on the contrary, is intended to cover such alternatives, modifications and equivalents as may be included within the spirit and scope of the invention as defined by the appended claims so that those skilled in the art should understand that they can make various changes, substitutions and alterations without departing from the spirit and scope of the invention in its broadest form.

Benefits, other advantages, and solutions to problems have been described above with regard to specific embodiments. However, the benefits, advantages, solutions to problems, and any element(s) that may cause any benefit, advantage, or solution to occur or become more pronounced are not to be construed as a critical, required, or essential feature or element of any or all the claims. As used herein, the terms “comprises,” “comprising,” or any other variation thereof, are intended to cover a non-exclusive inclusion, such that a process, method, article, or apparatus that comprises a list of elements does not include only those elements but may include other elements not expressly listed or inherent to such process, method, article, or apparatus.

## Claims

1. A communication method comprising:
estimating a downlink channel based on a signal received from a base station;
transmitting a first-precoding matrix index (PMI) to the base station periodically based on a first period;
transmitting a second-PMI to the base station periodically based on a second period;
receiving, from the base station, a downlink signal which includes precoded data symbols;
determining a precoding matrix to decode the received downlink signal; and
decoding the received downlink signal using the determined precoding matrix, wherein the first period and the second period are different from each other.

2. The method of claim 1, wherein the precoded data symbols are mapped one or two codewords into the layers.

3. The method of claim 1, wherein the first period is a multiple of the second period.

4. The method of claim 1, wherein the first PMI is used for a rank adaptation.

5. The method of claim 1, wherein the first PMI is used for a power allocation.

6. A communication apparatus comprising:
a processor; and
a memory operably coupled to the processor,
wherein the processor, when executing program instructions stored in the memory, is configured to:
cause the apparatus to estimate a downlink channel based on a signal received from a base station;
cause the apparatus to transmit a first-type precoding matrix index (PMI) to the base station periodically based on a first period;
cause the apparatus to transmit a second-type PMI to the base station periodically based on a second period;
cause the apparatus to receive from the base station, a downlink signal which includes precoded data symbols;
cause the apparatus to determine a precoding matrix to decode the received downlink signal; and
cause the apparatus to decode the received downlink signal using the determined precoding matrix, wherein the first period and the second period are different from each other.

7. The apparatus of claim 6, wherein the precoded data symbols are mapped one or two codewords into the layers.

8. The apparatus of claim 6, wherein the first period is a multiple of the second term period.

9. The apparatus of claim 6, wherein the first PMI is used for a rank adaptation.

10. The apparatus of claim 6, wherein the first PMI is used for a power allocation.

11. A mobile terminal comprising:
a processor; and
a memory operably coupled to the processor,
wherein the processor, when executing program instructions stored in the memory, is configured to:
cause the mobile terminal to estimate a downlink channel based on a signal received from a base station;
cause the mobile terminal to transmit a first-type precoding matrix index (PMI) to the base station periodically based on a first period;
cause the mobile terminal to transmit a second-type PMI to the base station periodically based on a second period;
cause the mobile terminal to receive from the base station, a downlink signal which includes precoded data symbols;
cause the mobile terminal to determine a precoding matrix to decode the received downlink signal; and
cause the mobile terminal to decode the received downlink signal using the determined precoding matrix,
wherein the first period and the second period are different from each other.

12. The mobile terminal of claim 11, wherein the precoded data symbols are mapped one or two codewords into the layers.

13. The mobile terminal of claim 11, wherein the first period is a multiple of the second period.

14. The mobile terminal of claim 11, wherein the first PMI is used for a rank adaptation.

15. The mobile of terminal of claim 11, wherein the first PMI is used for a power allocation.

