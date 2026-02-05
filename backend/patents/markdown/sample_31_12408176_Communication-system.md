# Communication system (Doc 12408176)

- Doc ID: 12408176
- Title: Communication system
- Filing Date: 20210730
- Classification: H04W 72/23
- Authors: Caroline Liang; Takahiro Sasaki

## Abstract

A method is disclosed in which downlink control information transmitted by a radio access network provides an indication of at least one set of control resources configured at a UE, or of at least one search space configured at a UE, that the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.

## Description

This application is a National Stage Entry of PCT/JP2021/028468 filed on Jul. 30, 2021, which claims priority from Great Britain Patent Application GB2012353.5 filed on Aug. 7, 2020, the contents of all of which are incorporated herein by reference, in their entirety.

The present invention relates to a communication system. The invention has particular but not exclusive relevance to wireless communication systems and devices thereof operating according to the 3rd Generation Partnership Project (3GPP) standards or equivalents or derivatives thereof (including LTE-Advanced and Next Generation or 5G networks). The invention has particular, although not necessarily exclusive relevance to, improved apparatus and methods that support flexible monitoring for the transmission of control information in a downlink control channel (e.g., a physical downlink control channel (PDCCH)).

Recent developments of the 3GPP standards are referred to as the Long Term Evolution (LTE) of Evolved Packet Core (EPC) network and Evolved UMTS Terrestrial Radio Access Network (E-UTRAN), also commonly referred as ‘4G’. In addition, the term ‘5G’ and ‘new radio’ (NR) refer to an evolving communication technology that is expected to support a variety of applications and services. Various details of 5G networks are described in, for example, the ‘NGMN 5G White Paper’ V1.0 by the Next Generation Mobile Networks (NGMN) Alliance, which document is available from https://www.ngmn.org/5g-white-paper.html. 3GPP intends to support 5G by way of the so-called 3GPP Next Generation (NextGen) radio access network (RAN) and the 3GPP NextGen core network.

Under the 3GPP standards, a NodeB (or an eNB in LTE, gNB in 5G) is the base station via which communication devices (user equipment or ‘UE’) connect to a core network and communicate to other communication devices or remote servers. For simplicity, the present application will use the term base station to refer to any such base stations.

In the current 5G architecture, for example, the gNB structure may be split into two parts known as the Central Unit (CU) and the Distributed Unit (DU), connected by an <i>F</i>1 interface. This enables the use of a ‘split’ architecture, whereby the, typically ‘higher’, CU layers (for example, but not necessarily or exclusively), PDCP) and the, typically ‘lower’, DU layers (for example, but not necessarily or exclusively, RLC/MAC/PHY) to be implemented separately. Thus, for example, the higher layer CU functionality for a number of gNBs may be implemented centrally (for example, by a single processing unit, or in a cloud-based or virtualised system), whilst retaining the lower layer DU functionality locally, in each of the gNB.

For simplicity, the present application will use the term mobile device, user device, or UE to refer to any communication device that is able to connect to the core network via one or more base stations. Although the present application often refers to mobile devices in the description, it will be appreciated that the technology described can be implemented on any communication devices (mobile and/or generally stationary) that can connect to a communications network for sending/receiving data, regardless of whether such communication devices are controlled by human input or software instructions stored in memory.

In 5G, the concept of a control resource set (CORESET) has been introduced. A CORESET is a set of time-frequency resources with which a UE can search for downlink control information (DCI) transmitted by a base station on a PDCCH. A CORESET is analogous to the control region at the start LTE subframes. However, unlike LTE, in which the frequency domain of the control region corresponds to the total system bandwidth, the frequency domain location for CORESET is localised to a specific region in frequency domain and has a variable width can be set to any suitable value (in the multiples of 6 resource blocks where each resource block comprises 12 subcarriers in the frequency domain).

A base station may transmit control information for a specific UE in a PDCCH that uses the resources of a UE specific CORESET defined for that UE. The PDCCH is made up of a number of control channel elements (CCEs) depending on the required aggregation level (L). Each CCE comprises a set of time/frequency resource comprising bundles of resource element groups, each group comprising a number of resource elements.

Allowing different UEs to be assigned different resource sets for their dedicated PDCCH signalling reduces but does not eliminate the probability of PDCCH blocking events in which there are no CCEs free for scheduling a given UE, at a particular aggregation level, in that UEs search space.

A number of different DCI formats can be used for transmission on a PDCCH and the transmitted format is unknown to the UE in advance. Accordingly, the UE typically needs to make multiple blind attempts to detect a DCI format. Whilst the CCE and CORESET structure helps in reducing the number of blind decoding attempts required this is not sufficient to reduce the number of blind decoding attempts to a practical level. To alleviate this issue, whilst still providing the base station with scheduling flexibility, a discrete number of search spaces are defined in which a UE is to search possible PDCCH resource locations (PDCCH ‘candidates’) for DCI. Each search space is a set of candidate PDCCHs formed by CCEs at a given aggregation level, which the UE can attempt to decode.

As there are a number of different possible aggregation levels there can be several search spaces for a given CORESET and, as there can be a number of CORESETs, the number of blind decoding attempts can still be relatively high. Thus, the respective number of PDCCH candidates for each PDCCH search space set is also configurable to allow blind decoding attempts to be spread across the search spaces for different aggregation levels.

Each PDCCH search space set can form a UE specific search space (USS) configured for a single UE, or a common search space (CSS), which is similar in structure to a USS but which has a set of CCEs that are predefined and hence known to all UEs.

Typically, at least the following five PDCCH search space sets are configured to support of the basic communication functionalities:

    
    
        A common search space set for system information block type 1 (SIB1),
        A common search space set for other system information,
        A common search space set for RACH,
        A common search space set for paging, and
        A UE-specific search space set for data transmission and reception.

Before a UE can attempt to decode a PDCCH candidate the UE must first perform channel estimation needs to be performed based on demodulation reference signals (DMRS) transmitted in the CCEs forming the PDCCH candidate. The number of PDCCH DMRS used to perform channel estimation depends on the number of CCEs forming the PDCCH candidate.

In order to reduce device complexity both the maximum number of blind decoding attempts that a UE is permitted to perform, and the number of CCEs on which channel estimation is performed, are limited depending on the subcarrier spacing and hence the slot duration. When a UE is searching for control information any unsearched PDCCH candidates will be skipped (or ‘dropped’) when either the number of blind decodes, or the number of CCEs, exceeds the maximum defined for the UE. This means that in some circumstances not all search spaces will be searched and so a rule is used to determine which search spaces should be searched first. According to this rule, common search space sets are prioritised over UE-specific search space sets, and UE-specific search space sets are prioritised based on their identities, with a USS having a smaller index being prioritised over a USS having a larger index.

At 3GPP Technical Standards Group (TSG) RAN Meeting #86, a new study was initiated for developing so called reduced capability (‘RedCap’ or ‘REDCAP’) UEs for a number of specific use cases including, but not limited to, industrial wireless sensing, video surveillance and wearable devices.

REDCAP UEs will typically: have a significantly reduced device complexity, compared to the high-end enhanced mobile broadband (eMBB) and ultra-reliable low-latency communication (URLLC) devices of earlier releases (especially for industrial sensors); support a reduced device size since most use cases require the capability for a device design with compact form factor; and support all the frequency bands of both 5G frequency ranges (i.e., FR1 and FR2) for both frequency division duplex (FDD) and time division duplex (TDD).

Each of the different use cases for REDCAP UEs has differing technical requirements making the design of communication protocols and apparatus that support REDCAP UEs more challenging. For example, the requirements for some of the key use cases may be summarised as follows:

Industrial Wireless Sensors

Communication service availability should ideally be at least 99.99% and end-to-end latency less than 100 ms. The reference bit rate should ideally be less than 2 Mbps (potentially uplink/downlink asymmetric e.g., because of uplink (UL) heavy traffic) for all use cases and the device is stationary. The battery should ideally last at least few years. For safety related sensors, the latency requirement may be lower, for example 5-10 ms.

Video Surveillance

Reference economic video bitrate capability would ideally be in the range 2-4 Mbps. Latency should ideally be less than 500 ms. Reliability should ideally be 99%-99.9%. High-end video, e.g., for farming, could require higher video bitrate capability in the range 7.5-25 Mbps. Traffic pattern dominated by UL transmissions should be supported.

Wearables Reference bitrate for smart wearable application capability would ideally be in the range 5-50 Mbps in downlink (DL) and 2-5 Mbps in UL. Peak bit rate capability of the device should ideally be higher—in the range 10-150 Mbps for DL and 5-50 Mbps for UL. The battery of the device should last multiple days (up to 1-2 weeks).

It can be seen that, for REDCAP UEs, power saving is an important design aspect, for example due to the smaller form factor and longer battery lifetime requirements. To help support such power saving, therefore, REDCAP UEs will typically have a reduced capability to monitor for control information on the PDCCH with tighter limits on the number of allowed blind decoding attempts and the maximum number of CCEs that can be subject to channel estimation.

Some REDCAP UEs may not support the usage of small aggregation levels, such as L=1 or L=2, while others may not be able to support high aggregation levels, e.g., L=16 due to bandwidth limitations.

Moreover, the PDCCH blocking probability may increase due to the potentially reduced bandwidth, potentially larger aggregation levels and/or potentially reduced number of CCEs that may be used for REDCAP UEs.

The invention aims to provide improved apparatus and methods that overcome or at least partially ameliorates the above issues.

Example aspects of the invention are set out in the appended independent claims. Optional but beneficial features are set out in the appended dependent claims.

According to one example aspect there is provided a method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising: receiving, from the radio access network, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information; monitoring for downlink control information (DCI) transmitted by the radio access network within the at least one search space within the at least one set of control resources; receiving, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information; and monitoring for DCI transmitted by the radio access network within the at least one search space within the set of control resources as reconfigured by the third information; wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.

According to one example aspect there is provided a method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising: obtaining information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration; and providing, to the radio access network, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE.

According to one example aspect there is provided a method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising: monitoring, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources; wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI; wherein the monitoring comprises, during a current slot of the monitoring occasion: (a) treating a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempting to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered; (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, selecting a remaining search space that has not been searched in the current slot to be searched next and repeating steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and (c) when an end to searching in the current slot is triggered, repeating steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered; wherein, before performing step (b), at least one USS is assigned to be a highest priority USS for the current slot; wherein, when selecting a search space to be searched next in step (b) the UE prioritises the remaining search spaces that have not been searched in the current slot based on based on a prioritisation scheme that requires that USSs are prioritised starting from a USS having a highest priority; and wherein the method further comprises, before repeating steps (a) to (c) during a subsequent slot of the monitoring occasion, reassigning a different USS to be highest priority USS.

According to one example aspect there is provided a method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising: monitoring, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources; wherein the set of control resources comprise at least one control channel element (CCE) and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI, each PDCCH candidate comprising at least one CCE; wherein the monitoring comprises, during a current slot of the monitoring occasion: (a) treating a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempting to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered; (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, selecting a remaining search space that has not been searched in the current slot to be searched next and repeating steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and (c) when an end to searching in the current slot is triggered, repeating steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered; wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues; wherein, the UE is configured with a maximum share of the maximum number of blind decode attempts that can be used for searching CSSs; and wherein, when selecting a search space to be searched next in step (b) the UE prioritises the remaining search spaces that have not been searched in the current slot based on a prioritisation scheme that requires that CSSs that have not been searched in the current slot are prioritised until further searching in a CSS will cause the maximum share of the maximum number of blind decode attempts to be exceeded, after which USSs that have not been searched in the current slot are prioritised.

According to one example aspect there is provided a method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising: monitoring, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources; wherein the set of control resources comprise at least one control channel element (CCE) and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI, each PDCCH candidate comprising at least one CCE; wherein the monitoring comprises, during a current slot of the monitoring occasion: (a) treating a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempting to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered; (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, selecting a remaining search space that has not been searched in the current slot to be searched next and repeating steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and (c) when an end to searching in the current slot is triggered, repeating steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered; wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current search space and the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues, even when the current search space has not been fully searched.

According to one example aspect there is provided a method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising: identifying a sequence of consecutive slots for forming a monitoring occasion; and monitoring, during the monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, within at least one set of control resources; wherein, when performing the monitoring, the UE monitors for control information in slots of the sequence of consecutive slots that are spaced apart by an unmonitored interval of at least one other slot of the sequence of consecutive slots.

According to one example aspect there is provided a user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising: a controller and a transceiver, wherein the controller is configured to control the transceiver to: receive, from the radio access network, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information; monitor for downlink control information (DCI) transmitted by the radio access network within the at least one search space within the at least one set of control resources; receive, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information; and monitor for DCI transmitted by the radio access network within the at least one search space within the set of control resources as reconfigured by the third information; wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.

According to one example aspect there is provided a user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising: a controller and a transceiver, wherein the controller is configured: to obtain information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration; and to control the transceiver to provide, to the radio access network, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE.

According to one example aspect there is provided a user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising: a controller and a transceiver, wherein the controller is configured to control the transceiver to: monitor, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources; wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI; wherein the controller is configured to control the UE, during a current slot of the monitoring occasion, to: (a) treat a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempt to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered; (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, select a remaining search space that has not been searched in the current slot to be searched next and repeat steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and (c) when an end to searching in the current slot is triggered, repeat steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered; wherein, before performing step (b), at least one USS is assigned to be a highest priority USS for the current slot; wherein the controller is configured to control the UE to, when selecting a search space to be searched next in step (b), prioritise the remaining search spaces that have not been searched in the current slot based on based on a prioritisation scheme that requires that USSs are prioritised starting from a USS having a highest priority; and wherein the controller is configured to control the UE to, before repeating steps (a) to (c) during a subsequent slot of the monitoring occasion, reassign a different USS to be highest priority USS.

According to one example aspect there is provided a user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising: a controller and a transceiver, wherein the controller is configured to control the transceiver to: monitor, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources; wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI; wherein the controller is configured to control the UE, during a current slot of the monitoring occasion, to: (a) treat a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempt to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered; (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, select a remaining search space that has not been searched in the current slot to be searched next and repeat steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and (c) when an end to searching in the current slot is triggered, repeat steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered; wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues; wherein, the UE is configured with a maximum share of the maximum number of blind decode attempts that can be used for searching CSSs; and wherein the controller is configured to control the UE to, when selecting a search space to be searched next in step (b), UE prioritise the remaining search spaces that have not been searched in the current slot based on a prioritisation scheme that requires that CSSs that have not been searched in the current slot are prioritised until further searching in a CSS will cause the maximum share of the maximum number of blind decode attempts to be exceeded, after which USSs that have not been searched in the current slot are prioritised.

According to one example aspect there is provided a user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising: a controller and a transceiver, wherein the controller is configured to control the transceiver to: monitor, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources; wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI; wherein the controller is configured to control the UE, during a current slot of the monitoring occasion, to: (a) treat a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempt to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered; (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, select a remaining search space that has not been searched in the current slot to be searched next and repeat steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and (c) when an end to searching in the current slot is triggered, repeat steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered; wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current search space and the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues, even when the current search space has not been fully searched.

According to one example aspect there is provided a user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising: a controller and a transceiver, wherein the controller is configured to identify a sequence of consecutive slots for forming a monitoring occasion, and to control the transceiver to monitor, during the monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, within at least one set of control resources; wherein the controller is configured to control the UE to monitor for control information in slots of the sequence of consecutive slots that are spaced apart by an unmonitored interval of at least one other slot of the sequence of consecutive slots.

According to one example aspect there is provided a method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising: transmitting, to the UE, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information; and transmitting, to the UE, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information; wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.

According to one example aspect there is provided a method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising: obtaining information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration; receiving, from the UE, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE; and configuring communication with the UE based on the received UE assistance information.

According to one example aspect there is provided a method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising: transmitting, to the UE, information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring a plurality of search spaces, comprising at least on UE specific search space (USS), within at least one set of control resources, wherein the information comprises information for configuring a maximum share of a maximum number of blind decode attempts that can be used by the UE for searching a common search space (CSSs).

According to one example aspect there is provided a method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising: transmitting, to the UE, information indicating a sequence of consecutive slots for forming a monitoring occasion, wherein the information comprises information for indicating an interval between slots of the sequence of consecutive slots that is to remain unmonitored by the UE.

According to one example aspect there is provided a radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising: a controller and a transceiver, wherein the controller is configured to control the transceiver to: transmit, to the UE, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information; and transmit, to the UE, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information; wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.

According to one example aspect there is provided a radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising: a controller and a transceiver, wherein the controller is configured: to obtain information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration; to control the transceiver to receive, from the UE, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE; and to configure communication with the UE based on the received UE assistance information.

According to one example aspect there is provided a radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising: a controller and a transceiver, wherein the controller is configured to control the transceiver to transmit, to the UE, information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring a plurality of search spaces, comprising at least on UE specific search space (USS), within at least one set of control resources, wherein the information comprises information for configuring a maximum share of a maximum number of blind decode attempts that can be used by the UE for searching a common search space (CSSs).

According to one example aspect there is provided a radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising: a controller and a transceiver, wherein the controller is configured to control the transceiver to transmit, to the UE, information indicating a sequence of consecutive slots for forming a monitoring occasion, wherein the information comprises information for indicating an interval between slots of the sequence of consecutive slots that is to remain unmonitored by the UE.

Example aspects of the invention extend to corresponding systems, apparatus, and computer program products such as computer readable storage media having instructions stored thereon which are operable to program a programmable processor to carry out a method as described in the example aspects and possibilities set out above or recited in the claims and/or to program a suitably adapted computer to provide the apparatus recited in any of the claims.

Each feature disclosed in this specification (which term includes the claims) and/or shown in the drawings may be incorporated in the invention independently of (or in combination with) any other disclosed and/or illustrated features. In particular but without limitation the features of any of the claims dependent from a particular independent claim may be introduced into that independent claim in any combination or individually.

Example embodiments of the invention will now be described, by way of example, with reference to the accompanying drawings in which:

FIG. <b>1</b> schematically illustrates a mobile (‘cellular’ or ‘wireless’) telecommunication system of FIG. <b>1</b>;

FIG. <b>2</b> illustrates a typical frame structure that may be used in the telecommunication system of FIG. <b>1</b>;

FIG. <b>3</b>A is a simplified illustration of a slot comprising a plurality of CORESETS in the telecommunication system of FIG. <b>1</b>;

FIG. <b>3</b>B is a simplified illustration of the relationship between a PDCCH candidate and the various different groupings of resources in the telecommunication system of FIG. <b>1</b>;

FIG. <b>4</b>A is a simplified illustration of a discontinuous reception (DRX) mechanism;

FIG. <b>4</b>B is a simplified illustration of the contents of a DCI format for notifying the power saving information outside of a DRX active time;

FIG. <b>5</b> is a schematic block diagram illustrating the main components of a user equipment for the telecommunication system shown in FIG. <b>1</b>;

FIG. <b>6</b> is a schematic block diagram illustrating the main components of a base station for the telecommunication system shown in FIG. <b>1</b>;

FIG. <b>7</b>A is a simplified illustration of a DRX cycle in which a wake-up signal is used to indicate whether or a UE should become active;

FIG. <b>7</b>B is another simplified illustration of another DRX cycle in which a wake-up signal is used to indicate whether or a UE should become active;

FIG. <b>8</b>A is a simplified timing diagram illustrating a procedure, which may be implemented in the telecommunication system of FIG. <b>1</b>;

FIG. <b>8</b>B is a simplified timing diagram illustrating another procedure, which may be implemented in the telecommunication system of FIG. <b>1</b>;

FIG. <b>9</b> is a simplified timing diagram illustrating another procedure, which may be implemented in the telecommunication system of FIG. <b>1</b>;

FIG. <b>10</b> is a simplified flow diagram illustrating a procedure which may be performed by a UE in the telecommunication system of FIG. <b>1</b>;

FIG. <b>11</b> is a simplified flow diagram illustrating another procedure which may be performed by a UE in the telecommunication system of FIG. <b>1</b>;

FIG. <b>12</b> is a simplified flow diagram illustrating another procedure which may be performed by a UE in the telecommunication system of FIG. <b>1</b>; and

FIG. <b>13</b> illustrates PDCCH monitoring during monitoring opportunities for the telecommunication system of FIG. <b>1</b>.

Overview

An exemplary telecommunication system will now be described, by way of example only, with reference to FIGS. <b>1</b> to <b>4</b>.

FIG. <b>1</b> schematically illustrates a mobile (‘cellular’ or ‘wireless’) telecommunication system <b>1</b> to which example embodiments of the present invention are applicable.

In the network <b>1</b> user equipment (UEs) <b>3</b>-<b>1</b>, <b>3</b>-<b>2</b>, <b>3</b>-<b>3</b> (e.g., mobile telephones and/or other mobile devices) can communicate with each other via base stations <b>5</b> can communicate with each other via a radio access network (RAN) node <b>5</b> that operates according to one or more compatible radio access technologies (RATs). In the illustrated example, the RAN node <b>5</b> comprises a NR/5G base station or ‘gNB’ <b>5</b> operating one or more associated cells <b>9</b>. Communication via the base station <b>5</b> is typically routed through a core network <b>7</b> (e.g., a 5G core network or evolved packet core network (EPC)).

As those skilled in the art will appreciate, whilst three UEs <b>3</b> and one base station <b>5</b> are shown in FIG. <b>1</b> for illustration purposes, the system, when implemented, will typically include other base stations and UEs.

Each base station <b>5</b> controls the associated cell(s) either directly, or indirectly via one or more other nodes (such as home base stations, relays, remote radio heads, distributed units, and/or the like). It will be appreciated that the base stations <b>5</b> may be configured to support both 4G and 5G, and/or any other 3GPP or non-3GPP communication protocols.

The UEs <b>3</b> and their serving base station <b>5</b> are connected via an appropriate air interface (for example the so-called ‘Uu’ interface and/or the like). Neighbouring base stations <b>5</b> may be connected to each other via an appropriate base station to base station interface (such as the so-called ‘X2’ interface, ‘Xn’ interface and/or the like).

The core network <b>7</b> includes a number of logical nodes (or ‘functions’) for supporting communication in the telecommunication system <b>1</b>. In this example, the core network <b>7</b> comprises control plane functions (CPFs) <b>10</b> and one or more user plane functions (UPFs) <b>11</b>. The CPFs <b>10</b> include one or more Access and Mobility Management Functions (AMFs) <b>10</b>-<b>1</b>, one or more Session Management Functions (SMFs) and a number of other functions <b>10</b>-<i>n. </i>

The base station <b>5</b> is connected to the core network nodes via appropriate interfaces (or ‘reference points’) such as an N2 reference point between the base station <b>5</b> and the AMF <b>10</b>-<b>1</b> for the communication of control signalling, and an N3 reference point between the base station <b>5</b> and each UPF <b>11</b> for the communication of user data. The UEs <b>3</b> are each connected to the AMF <b>10</b>-<b>1</b> via a logical non-access stratum (NAS) connection over an N1 reference point (analogous to the S1 reference point in LTE). It will be appreciated, that N1 communications are routed transparently via the base station <b>5</b>.

The UPF(s) <b>11</b> are connected to an external data network (e.g., an IP network such as the internet) via reference point N6 for communication of the user data.

The AMF <b>10</b>-<b>1</b> performs mobility management related functions, maintains the non-NAS signalling connection with each UE <b>3</b> and manages UE registration. The AMF <b>10</b>-<b>1</b> is also responsible for managing paging. The SMF <b>10</b>-<b>2</b> provides session management functionality (that formed part of MME functionality in LTE) and additionally combines some control plane functions (provided by the serving gateway and packet data network gateway in LTE). The SMF <b>10</b>-<b>2</b> also allocates IP addresses to each UE <b>3</b>.

In this example, one of the UEs <b>3</b>-<b>1</b> is a so called reduced capability (REDCAP) UE, for example a UE having a reduced device complexity (compared to the high-end enhanced mobile broadband (eMBB) and ultra-reliable low-latency communication (URLLC) devices of earlier releases, that supports a compact form factor, and that supports the frequency bands of FR1 and FR2 for both FDD TDD.

Referring to FIG. <b>2</b>, which illustrates the typical frame structure that may be used in the telecommunication system <b>1</b>, the base station <b>5</b> and UEs <b>3</b> of the telecommunication system <b>1</b> communicate with one another using resources that are organised, in the time domain, into frames of length 10 ms. Each frame comprises ten equally sized subframes of 1 ms length. Each subframe is divided into one or more slots comprising 14 Orthogonal frequency-division multiplexing (OFDM) symbols of equal length.

[Math. 1]

As seen in FIG. <b>2</b>, the telecommunication system <b>1</b> supports mule different numerologies (subcarrier spacing (SCS), slot lengths and hence OFDM symbol lengths). Specifically, each numerology is identified by a parameter, μ, where μ=0 represents 15 kHz (corresponding to the LTE SCS). Current, the SOS for other values of μ can, in effect, be derived from μ=0 by scaling up in powers of 2 (i.e., SOS 15×2<sup>μ</sup>KHz) The relationship between the parameter, μ, and SOS (Δf) is as shown in Table 1:

[Table 1]

TABLE 1







5G Numerology














Number of slots
Slot length (ms)



μ
Δf = 2<sup>μ</sup> · 15 [kHz]
per subframe
















0
15
1
1



1
30
2
0.5



2
60
4
0.25



3
120
8
0.125



4
240
16
0.0625

Referring to FIG. <b>3</b>, FIG. <b>3</b>A is a simplified illustration of a slot comprising a plurality of CORESETS in the telecommunication system of FIG. <b>1</b>, and FIG. <b>3</b>B is a simplified illustration of the relationship between a PDCCH candidate and the various different groupings of resources in the telecommunication system of FIG. <b>1</b>.

As seen in FIG. <b>3</b>A, the base station <b>5</b> of the telecommunication system <b>1</b>, can configure a UE <b>3</b>, such as the REDCAP UE <b>3</b>-<b>1</b>, with one or more CORESETs <b>310</b>. comprising a set of time-frequency resources with which the UE <b>3</b> can search for downlink control information (DCI) transmitted by the base station <b>5</b> on a PDCCH. Each CORESET may be up to 3 OFDM symbols in length. The CORESET configured for a UE <b>3</b> will typically include one or more UE specific CORESETs configured, for example, by RRC signalling, and one or more common CORESETs configured by system information, for example, by a master information block (MIB). For example, the base station <b>5</b> is configured to use the MIB to configure an initial CORESET (CORESET 0) in which to search for a PDCCH providing scheduling for the physical downlink shared channel (PDSCH) providing system information block type 1 (SIB1).

The base station <b>5</b> may therefore transmit downlink control information (DCI) for a specific UE <b>3</b> in a PDCCH that uses the resources of a UE specific CORESET defined for that UE <b>3</b>.

[Math. 2]

As seen in FIG. <b>3</b>B, a PDCCH is made up of a number of (typically 1, 2, 4, 8, 16) control channel elements (CCEs) depending on the required aggregation level (L∈{2, 4, 8, 16}). Each CCE is made up of a number of (typically 1, 2 or 3) resource element group bundles (REG bundles) each comprising a number of resource element groups (REGs) made up of resource elements (REs). Each RE is effectively the smallest unit of the resource grid is made up of one subcarrier in the frequency domain and one OFDM symbol in time domain. A REG corresponds to one resource block (i.e., 12 REs/subcarriers) in the frequency domain and one OFDM symbol time domain.

A number of search spaces may be configured dynamically by the base station <b>5</b>, or may be predefined, in which a UE <b>3</b> may search for DCI. Each search space comprises a set of candidate PDCCHs formed by CCEs of a CORESET at a given aggregation level, which the UE <b>3</b> can attempt to decode. The search spaces may include one or more UE specific search spaces (USSs) configured for a single UE (e.g., using RRC signalling from the base station to the UE) and/or one or more common search spaces (CSSs) that are predefined and hence known to all UEs <b>3</b> in advance.

For example, the following five PDCCH search space sets are typically configured to support of the basic communication functionalities:

    
    
        A common search space set for system information block type 1 (SIB1), A common search space set for other system information,
        A common search space set for RACH,
        A common search space set for paging, and
        A UE-specific search space set for data transmission and reception.

The parameters configuring each CORESET define the time/frequency resources of that CORESET in which to search for downlink control information. Each CORESET may be identified by a CORESET identifier/index (e.g., using a ControlResourceSetID IE or the like). The parameters configuring each search space define how/where to search for PDCCH candidates in a CORESET with which that search space is associated. Each search space may be identified by a search space identifier/index (e.g., using a SearchSpaceID or the like). Each search space may be associated with one or more additional search spaces that form part of a group of search spaces or a ‘search space set’ by means of by means of a common group identifier or index (e.g., a searchSpaceGroupId or the like).

The UEs <b>3</b> are configured to perform channel estimation needs based on demodulation reference signals (DMRS) transmitted by the base station in the CCEs forming a PDCCH candidate before any attempt is made to decode any control DCI provided in that PDCCH candidate.

A number of different DCI formats can be used by the base station <b>5</b>, depending on requirements, for transmission on a PDCCH corresponding to one of the PDCCH candidates in one of the search spaces configured for a given UE <b>3</b>. For example, the base station <b>5</b> may be able to transmit DCI using one or more of the currently standardised DCI formats as set out in Table 2:

[Table 2]

TABLE 2







DCI Format Summary








DCI format
Usage





0_0
Scheduling of PUSCH in one cell


0_1
Scheduling of one or multiple PUSCH in one cell, 



or indicating downlink feedback information for 



configured grant PUSCH (CG-DFI)


0_2
Scheduling of PUSCH in one cell


1_0
Scheduling of PDSCH in one cell


1_1
Scheduling of PDSCH in one cell, and/or triggering 



one shot HARQ-ACK codebook feedback


1_2
Scheduling of PDSCH in one cell


2_0
Notifying a group of UEs of the slot format, 



available RB sets, COT duration and search space 



set group switching


2_1
Notifying a group of UEs of the PRB(s) and OFDM 



symbol(s) where UE may assume no transmission is 



intended for the UE


2_2
Transmission of TPC commands for PUCCH and PUSCH


2_3
Transmission of a group of TPC commands for SRS



transmissions by one or more UEs


2_4
Notifying a group of UEs of the PRB(s) and OFDM 



symbol(s) where UE cancels the corresponding UL 



transmission from the UE


2_5
Notifying the availability of soft resources as defined 



in Clause 9.3.1 of 3GPP TS 38.473.


2_6
Notifying the power saving information outside DRX 



Active Time for one or more UEs


3_0
Scheduling of NR sidelink in one cell


3_1
Scheduling of LTE sidelink in one cell

The REDCAP UEs reduced capability may mean that it does not monitor for all of these DCI formats. For example, the REDCAP UE <b>3</b>-<b>1</b> would typically not have the capability to monitor DCI format 2_0 (Slot Format Indicators) on a licensed band for search space set group switching.

Referring to FIG. <b>4</b>, FIG. <b>4</b>A is a simplified illustration of a discontinuous reception (DRX) mechanism, and FIG. <b>4</b>B is a simplified illustration of the contents of a DCI format for notifying the power saving information outside of a DRX active time for one or more UEs.

Each UE <b>3</b> is configured to be able to implement a number of power saving functions including the ability to operate in a DRX mode, similar to that illustrated in FIG. <b>4</b>A in which the UE <b>3</b> is configured to switch off radio frequency circuitry and front-end hardware during a DRX inactive, sleep, or ‘OFF’ period, of a DRX cycle, and to switch the circuitry and hardware on during an active or ‘ON’ period of the DRX cycle in order to monitor for and receive control information, such as scheduling information, on a PDCCH.

However, in the case of sporadic traffic, it can be inefficient for a UE <b>3</b> to periodically wake up to monitor PDCCH candidates every DRX ON period before returning to an inactive state during the OFF period. Accordingly, each UE <b>3</b> including the REDCAP UES <b>3</b>-<b>1</b>, is configured to continue monitoring for a special DCI format (DCI format 2_6) during the OFF period. The DCI format includes a wake-up signal (WUS) field <b>410</b> that is used to inform a given UE <b>3</b> whether or not to wake up at the start of the ON period of the next DRX cycle, for potential data scheduling.

As seen in FIG. <b>4</b>A, in the current version of DCI format 2_6 the WUS field <b>410</b> comprises a single bit that is set to ‘1’ to indicate to a UE <b>3</b> that it should wake up and a ‘0’ to indicate to the UE <b>3</b> that it should not wake up.

As seen in FIG. <b>4</b>B, DCI format 2_6 also includes a secondary cell (SCell) dormancy indication to indicate whether or not one or more SCells should remain dormant after the UE wakes up. To reduce the blocking rate and resource overhead, DCI format 2_6 can be used to convey multiple WUS <b>410</b>-<b>1</b> to <b>410</b>-<i>n </i>and SCell dormancy indications <b>412</b>-<b>1</b> to <b>412</b>-<i>n </i>for one or more UEs in a group, where each UE in the group is configured with the location of the wake-up indication.

Beneficially, the telecommunication network <b>1</b> implements a number of advantageous procedures and features. These procedures and features are particularly beneficial in the context of REDCAP UEs but may be extended to other types of UEs to provide additional PDCCH monitoring flexibility, reliability and/or efficiency. It will be appreciated that these procedures and features are neither dependent on one another, nor mutually exclusive, and so could be implemented individually in isolation from one another or in combination.

Dynamic CORESET/search space ON/OFF For example, the telecommunication network <b>1</b> beneficially implements a number of procedures for allowing CORESETs and/or search spaces to be switched on, or off, dynamically, for a given UE <b>3</b>.

In a particularly advantageous procedure, the base station <b>5</b> is able to configure the UE <b>3</b> to reconfigure the CORESETs and/or search spaces as soon as the UE <b>3</b> wakes up from the inactive or OFF part of the DRX cycle. Specifically, in the telecommunication system <b>1</b>, DCI format 2_6 is modified to notify each UE <b>3</b>, outside of the DRX active time, of the CORESET(s) and/or search space set(s) that are to be monitored by the UE <b>3</b>, when the UE <b>3</b> wakes up and becomes active during the DRX ON period.

Advantageously, the WUS field of DCI format 2_6 is modified to provide an indication of each CORESET and/or PDCCH search space set that is to be monitored by the UE <b>3</b>.

The base station <b>5</b> is therefore able to dynamically configure the UEs <b>3</b>, and in particular the REDCAP UE <b>3</b>-<b>1</b>, to update the CORESET(s) and/or search space set(s) that are to be monitored following a period of sleep, for example when some of the originally configured CCEs are being occupied by other, active, UEs <b>3</b> and the risk of blocking is therefore high. Thus, dynamic search space ‘ON/OFF’ is supported by the UEs <b>3</b>, including the REDCAP UE <b>3</b>-<b>1</b>, and can be applied, in conjunction with the DRX operation mode, to ensure that the UE <b>3</b> begins to monitor the correct search spaces/CORESET as soon as the UE wakes up.

This approach thus allows for a reduction in the number of simultaneously monitored search space sets and allows an active search space set to be dynamically reconfigured at the same time as the UE wakes up, with no increase to PDCCH monitoring. It can be seen, therefore, that the CORESET/search space can beneficially be configured based on data traffic and thereby reduce the number of blind decoding attempts and the blocking probability while maintaining scheduling flexibility.

It will be appreciated that, when the UE <b>3</b> is in the active state, if some of the configured search space sets are being blocked by other (higher priority) UEs, it may also be beneficial for the UEs <b>3</b>, and in particular the REDCAP UE <b>3</b>-<b>1</b>, to be able to update the search space sets monitored.

Accordingly, in another particularly advantageous procedure, the base station <b>5</b> is able to configure the UE <b>3</b> to reconfigure the CORESETs and/or search spaces while the UE <b>3</b> is active, for example during the ON period of the DRX cycle. Specifically, the telecommunication system <b>1</b> also implements a modified DCI format 1_1 and/or 0_1 that can be used by the base station <b>5</b> to reconfigure the CORESET and/or the associated PDCCH search space sets monitored by the UEs <b>3</b>, and in particular the REDCAP UE <b>3</b>-<b>1</b>, during the active time. Beneficially, in this example, to avoid an increase in the DCI size, one or more existing fields of the DCI format is repurposed for providing an indication an indication of each CORESET and/or PDCCH search space set that is to be monitored by the UE <b>3</b>. Beneficially, therefore there is no increase in PDCCH monitoring arising from the change. Specifically, in this example the Code Block Group (CBG) transmission information (CBGTI) fields are reused although it will be appreciated that a different field could, alternatively, be repurposed. It will, nevertheless, be appreciated that a different existing field may be repurposed to provide the indication, or an additional dedicated field could be added instead of a repurposed field.

It will be appreciated that the modification of DCI format 1_1/0_1 may be used instead of, or in conjunction with, the modification of DCI format 2_6. The field used in DCI format 1_1, 0_1 or 2_6 to reconfigure the CORESETs and/or search spaces may, for example, be in the form of a bitmap having a separate bit representing the ON/OFF configuration for each CORESET and/or search space set that the UE <b>3</b> that the UE <b>3</b> may be configured with (e.g., where ‘1’ indicates ‘ON’; ‘0’ indicates ‘OFF’ or vice versa). For example, if a REDCAP UE <b>3</b>-<b>1</b> can support three search space sets, three bits may be introduced in DCI for dynamic indication for switching three active search space sets on or off, where ‘1’ indicates ‘ON’; ‘0’ indicates ‘OFF’.

After the RRC connection is established, the search space sets for SIB1 and other system information may, beneficially, be released to reduce the number of simultaneously monitored search space sets and hence the number of blind decoding attempts. Moreover, the search space sets for other functionalities could be configured in place of the released search space sets. For example, the PDCCH search space sets to be searched by the UE <b>3</b> could be reconfigured to control information relating to pre-emption, slot format indication (SFI), group transmit power control (TPC), power saving, and/or the like.

Beneficially, in the telecommunication system <b>1</b>, the maximum number of simultaneously monitored search space sets by the UE <b>3</b> is configurable (for example to between 3 to 8 inclusive). It will be appreciated that the maximum number of simultaneously monitored search space sets may be configured using RRC signalling, or may be configured by UE power saving assistance information for the UE <b>3</b>, from which the base station <b>5</b> can derive an appropriate value for the UE's specific configuration.

UE Assistance Information for Reduced PDCCH Monitoring

To support the various types of terminal and service, multiple reduced PDCCH monitoring capabilities may be configured in the telecommunications system <b>1</b> for REDCAP UEs <b>3</b>-<b>1</b>. To support this the REDCAP UE <b>3</b>-<b>1</b> is beneficially configured to report its reduced PDCCH monitoring capability to the base station.

However, to mitigate the network complexities and inefficiencies that may arise from freely reporting different sets of UE capabilities in an unrestricted manner, a UE power saving preference table, or set of sub-tables, is configured that defines a plurality of different UE power saving configurations, each power saving configuration representing a different respective set of parameters. An indication of the power saving configuration of a particular UE <b>3</b> is, in this example, reported by that UE <b>3</b> to the base station <b>5</b> as part of UE assistance information. The base station <b>5</b> is configured to determine, from the received indication, a set of requirements for configuring the UE <b>3</b> appropriately based on the corresponding power saving configuration.

PDCCH Candidate Dropping

Each UE <b>3</b> is preconfigured with a maximum number of blind decode attempts, and a maximum number of CCEs used for channel estimation purposes within a given slot. When a UE <b>3</b> is searching for control information any unsearched PDCCH candidates will be skipped (or ‘dropped’) when either the number of blind decodes, or the number of CCEs, exceeds the maximum defined for the UE <b>3</b> in that slot.

This gives rise to the possibility that some search spaces, especially high index USSs will be searched only rarely, if at all. This is a particular issue for REDCAP UEs in which the maximum number of blind decode attempts, and maximum number of CCEs used for channel estimation purposes, may be reduced.

Accordingly, the telecommunication system <b>1</b> beneficially implements a modified set of rules for determining which search spaces should be monitored. Specifically, the telecommunication system can implement one or more of the following rule variations to provide an improved balance among search space sets and thus improve PDCCH detection performance.

In one rule variation, once every CSS has been searched, rather than always starting with the lowest index USS, the first USS searched by the UE changes from slot to slot. This can be achieved by assigning the highest priority to a different USS each slot. For example, the highest priority USS may be cycled from slot-to-slot starting from the USS having the lowest index in a first slot, before being reassigned to the USS having the next lowest index, in ascending order, in the next slot, and so on. The USSs are then searched, starting from the highest priority USS, in order of increasing USS index. When the highest index USS has been searched, if there are any unsearched lower index USSs (and the maximum blind decodes/CCEs has not been reached) the UE returns to the lowest index USS and the continues to search the unsearched USSs in order of increasing USS index from the lowest index USS. After the USS having the highest index has been assigned the highest priority the procedure can essentially restart, in the next slot, with the lowest index USS being assigned the highest priority.

In another rule variation, the maximum number of blind decode attempts is essentially shared between CSSs and USSs (e.g., based on a fractional value or the like configured at the UE <b>3</b>). Once the share of blind decoding attempts has been reached for CSS searching the UE <b>3</b> begins to search the USSs until the maximum number of blind decode attempts or maximum number of CCEs is reached (or there are no more USSs to search). If all USSs have been searched and the maximum number of blind decode attempts has not been reached then any remaining CSS can be searched. It will be appreciated that prioritisation of the USS may be in increasing order of USS index, or based on cycling of the highest priority USS described above. Moreover, in addition to, or as an alternative to, sharing the maximum number of blind decode attempts the maximum number of CCEs could be shared between the USSs or CSSs.

In current systems, during the searching process, if the number of PDCCH candidates in a given search space (e.g., a USS) is larger than the number that can be searched without exceeding the maximum number of blind decode attempts (and/or maximum number of CCEs), then the whole search space set is dropped without any PDCCH candidate being searched of that search space set.

Beneficially, in another rule variation, the UE <b>3</b> is configured to continue to search PDCCH candidates of a search space set, until the maximum number of blind decode attempts (and/or maximum number of CCEs) is reached, even when the number of PDCCH candidates of that search space set is larger than the number that can be searched without exceeding the maximum number of blind decode attempts (and/or maximum number of CCEs).

Discontinuous PDCCH Monitoring

In order to know when to search for control information the UEs <b>3</b> are configured to determine a PDDCH monitoring occasion, typically comprising a plurality of slots, within which it should search for the control information. Beneficially, in the telecommunication system <b>1</b>, the UEs <b>3</b> are configurable to be able to monitor for the PDCCH either continuously in every consecutive slot or discontinuously every other slot or every few slots.

This is particularly beneficial for supporting a higher number of UE connections, taking account the short symbol durations that may be used for PDCCH monitoring in higher numerologies (e.g., for supporting the higher frequency bands of frequency range FR2).

User Equipment

FIG. <b>5</b> is a schematic block diagram illustrating the main components of a UE <b>3</b> as shown in FIG. <b>1</b>, and in particular the REDCAP UE <b>3</b>-<b>1</b> (e.g., an industrial wireless sensor, surveillance video equipment, wearable device, or other user equipment). It will be appreciated that while the UE <b>3</b> is described as being a REDCAP UE, the UE <b>3</b> may be configured for operating as another, non-REDCAP, UE <b>3</b>.

As shown, the UE <b>3</b> has a transceiver circuit <b>31</b> that is operable to transmit signals to and to receive signals from a base station <b>5</b> via one or more antenna <b>33</b>. The UE <b>3</b> has a controller <b>37</b> to control the operation of the UE <b>3</b>. The controller <b>37</b> is associated with a memory <b>39</b> and is coupled to the transceiver circuit <b>31</b>. Although not necessarily required for its operation, the UE <b>3</b> might, of course, have all the usual functionality of a conventional UE <b>3</b> (e.g., a user interface <b>35</b>, such as a touch screen/keypad/microphone/speaker and/or the like for, allowing direct control by and interaction with a user) and this may be provided by any one or any combination of hardware, software and firmware, as appropriate. Software may be pre-installed in the memory <b>39</b> and/or may be downloaded via the telecommunications network or from a removable data storage device (RMD), for example.

The controller <b>37</b> is configured to control overall operation of the UE <b>3</b> by, in this example, program instructions or software instructions stored within memory <b>39</b>. As shown, these software instructions include, among other things, an operating system <b>41</b>, a communications control module <b>43</b>, a control information management module <b>45</b>, a power saving management module <b>47</b>, an assistance information management module <b>49</b>, an RRC module <b>51</b>, and a system information module <b>53</b>.

The communications control module <b>43</b> is operable to control the communication between the UE <b>3</b> and its serving base station(s) <b>5</b> (and other communication devices connected to the base station <b>5</b>, such as further UEs and/or core network nodes). The communications control module <b>43</b> is configured for the overall handling uplink communications via associated uplink channels (e.g., via a physical uplink control channel (PUCCH) and/or a physical uplink shared channel (PUSCH)) and for handling receipt of downlink communications via associated downlink channels (e.g., via a physical downlink control channel (PDCCH) and/or a physical downlink shared channel (PDSCH)). The communications control module <b>43</b> is responsible for determining the resources to be used by the UE <b>3</b> and to determine which bandwidth part (or sub-band) is allocated for the UE <b>3</b> (e.g., based on a bandwidth supported by the transceiver circuit <b>31</b>).

The control information management module <b>45</b> is responsible for managing the tasks related to the reception of downlink control information from the base station. These tasks include, but are not limited to: identifying monitoring occasions within which to search for control information; configuring and reconfiguring the CORESETs and the search spaces within which to search PDCCH candidates; monitoring for downlink control information in CSSs and/or USSs a including performing channel estimation and conducting the related searches; decoding downlink control information transmitted to the UE <b>3</b> by the base station using an appropriate DCI format.

The power saving management module <b>47</b> is responsible for managing power saving tasks at the UE <b>3</b>, for example: operation in a DRX mode; switching the appropriate parts of the transceiver circuit <b>31</b> ON or OFF at appropriate time in a DRX cycle for example by responding to a WUS provided by the base station <b>5</b>, using DCI format 2_6, and received and decoded by the control information management module <b>45</b>. The power saving management module <b>47</b> maintains the UE power saving preference table.

The assistance information management module <b>49</b> manages the generation of UE assistance information for assisting the base station <b>5</b> to configure communication with the UE appropriately, and the sending of that UE assistance information to the base station <b>5</b> when required. The assistance information may include any appropriate information relating to the UE's capabilities and/or configuration, for example an indication of the UEs power saving configuration.

The RRC module <b>51</b> is responsible for the reception of RRC signalling from the base station <b>5</b>, and the transmission of RRC signalling to the base station <b>5</b>.

The system information module <b>53</b> is responsible for the reception of system information from the base station <b>5</b>.

Base Station

FIG. <b>6</b> is a schematic block diagram illustrating the main components of the base station <b>5</b> for the telecommunication system <b>1</b> shown in FIG. <b>1</b>. As shown, the base station <b>5</b> has a transceiver circuit <b>51</b> for transmitting signals to and for receiving signals from the communication devices (such as UEs <b>3</b>) via one or more antenna <b>53</b> (e.g., an antenna array/massive antenna), and a core network interface <b>55</b> (e.g., comprising the N2, N3 and other reference points/interfaces) for transmitting signals to and for receiving signals from network nodes in the core network <b>7</b>. Although not shown, the base station <b>5</b> may also be coupled to other base stations via an appropriate interface (e.g., the so-called ‘Xn’ interface in NR). The base station <b>5</b> has a controller <b>57</b> to control the operation of the base station <b>5</b>. The controller <b>57</b> is associated with a memory <b>59</b>. Software may be pre-installed in the memory <b>59</b> and/or may be downloaded via the communications network <b>1</b> or from a removable data storage device (RMD), for example. The controller <b>57</b> is configured to control the overall operation of the base station <b>5</b> by, in this example, program instructions or software instructions stored within memory <b>59</b>.

As shown, these software instructions include, among other things, an operating system <b>61</b>, a communications control module <b>63</b>, a control information management module <b>65</b>, a power saving management module <b>67</b>, an assistance information management module <b>69</b>, an RRC module <b>71</b>, and a system information module <b>73</b>.

The communications control module <b>63</b> is operable to control the communication between the base station <b>5</b> and UEs <b>3</b> and other network entities that are connected to the base station <b>5</b>. The communications control module <b>63</b> is configured for the overall control of the reception of uplink communications, via associated uplink channels (e.g., via a physical uplink control channel (PUCCH) and/or a physical uplink shared channel (PUSCH)) and for handling the transmission of downlink communications via associated downlink channels (e.g., via a physical downlink control channel (PDCCH) and/or a physical downlink shared channel (PDSCH)).

The control information management module <b>65</b> is responsible for managing the tasks related to the transmission of downlink control information from the base station. These tasks include, but are not limited to: generating parameters for use by a UE <b>3</b> in identifying monitoring occasions within which to search for control information and transmitting those parameters to the UE <b>3</b>; generating configuration information for configuring (and reconfiguring) the CORESETs and search spaces within which to search PDCCH candidates; generating downlink control information for reception by a particular UE <b>3</b>, or group of UEs <b>3</b>, and the transmission of that downlink control information using a PDCCH in a corresponding PDCCH candidate of a search space using an appropriate DCI format.

The power saving management module <b>67</b> is responsible for managing power saving for the UE <b>3</b> from the base station side. This may include, for example, triggering of UE <b>3</b> to wake-up from an inactive state by using a WUS provided to the UE <b>3</b>, using DCI format 2_6. The power saving management module <b>67</b> may also be responsible for triggering the sending of configuration information for configuring the power saving preference table at the UE <b>3</b> (if the table is configured by the base station <b>5</b>).

The assistance information management module <b>69</b> manages the reception and interpretation of UE assistance information for assisting the base station <b>5</b> to configure communication with the UE appropriately from the UE <b>3</b>. The assistance information may include any appropriate information relating to the UE's capabilities and/or configuration, for example an indication of the UEs power saving configuration.

The RRC module <b>71</b> is responsible for the reception of RRC signalling from UE <b>3</b>, and the transmission of RRC signalling to the UE <b>3</b>.

The system information module <b>73</b> is responsible for the transmission of system information to UEs in the base station's cell(s) <b>9</b>.

Dynamic CORESET/search space ON/OFF The different possible mechanisms for providing dynamic reconfiguration of the CORESET(s)/search space(s) will now be described in more detail, by way of example only, with reference to FIGS. <b>7</b> and <b>8</b>.

DCI Format 2_6

FIG. <b>7</b>A is a simplified illustration of a DRX cycle in which a wake-up signal is used to indicate whether or not a given UE <b>3</b> should become active during an ON period of the DRX cycle. As seen in FIG. <b>7</b>A, the WUS field <b>410</b> of DCI format 26 is set to provide a CORESET ON/OFF indication and/or a search space ON/OFF indication before the UE <b>3</b> wakes up.

In this example, the WUS field <b>410</b> is provided in the form of a bitmap having a separate bit representing the ON/OFF configuration for each CORESET and/or each search space set that the UE <b>3</b> that the UE <b>3</b> may be configured with (e.g., where ‘1’ indicates ‘ON’; ‘0’ indicates ‘OFF’ or vice versa). The mapping of each bit of the WUS field to a specific CORESET (and hence the associated search space(s) configured for that CORESET) may be based on the CORESET identifier/index (e.g., the controlResourceSetId IE) with each bit representing a different configured CORESET in ascending (or descending) order of CORESET identifier.

The mapping of each bit of the WUS field to a specific search space set (or group of search space sets) may be based on the search space (e.g., using a SearchSpaceID or the like), or a common search space group identifier/index (e.g., a searchSpaceGroupId or the like), with each bit representing a different configured search space set, or group of search space sets, in ascending (or descending) order of the identifier/index.

It will be appreciated that that the WUS field may be set to all zeros to indicate that the UE <b>3</b> should not wake up for the next DRX cycle.

FIG. <b>8</b>A is a simplified timing diagram illustrating a procedure, which may be implemented in the telecommunication system <b>1</b> of FIG. <b>1</b> and in which the WUS field of DCI format 2_6 is used to provide a CORESET ON/OFF indication and/or a search space ON/OFF indication before the UE <b>3</b> wakes up.

As seen in FIG. <b>8</b>A when the UE <b>3</b> operating in a DRX mode and is in a DRX inactive state during the DRX OFF period it does, nevertheless, monitor for control information in DCI format 2_6 at S<b>810</b>. When the base station <b>5</b> determines, at S<b>812</b> that the UE <b>3</b> is to wake up, it determines an appropriate CORESET and/or search space set configuration. The base station <b>5</b> then sends, at S<b>814</b>, downlink control information, using DCI Format 2_6, with the WUS field set to provide the corresponding CORESET ON/OFF indication and/or a search space ON/OFF indication representing the new configuration.

The UE <b>3</b> moves to an active state at the start of the next DRX ON period and configures its CORESET(s) and/or search space set(s) appropriately based on the content of the WUS field at S<b>816</b>.

DCI Format 0_1/1_1 FIG. <b>7</b>B is a simplified illustration of a DRX cycle in which a wake-up signal is used to indicate whether or not a given UE <b>3</b> should become active during the next ON period of the DRX cycle. In FIG. <b>7</b>B the WUS signal may form part of a conventional DCI 2_6 in which the WUS field <b>410</b> is a single bit or a WUS field as described with reference to FIG. <b>7</b>A in which the WUS field <b>410</b> provides a CORESET ON/OFF indication and/or a search space ON/OFF indication before the UE <b>3</b> wakes up.

As seen in FIG. <b>7</b>B, when the UE <b>3</b> is active during the ON period of the DRX cycle DCI <b>710</b> is provided by the base station <b>5</b> using DCI format 0_1 (as summarised in Table 3) and/or DCI 1_1 (as summarised in Table 4). This DCI <b>710</b> is configured to provide a CORESET ON/OFF indication and/or a search space ON/OFF indication when reconfiguration of the CORESET(s) and/or a search space set(s) is required.

[Table 3]

TABLE 3







DCI Format 0_1








Field
Bits





Identifier for Downlink Control Information (DCI) formats
1


Carrier indicator
0 or 3


Downlink Feedback Information (DFI) Flag
0, 1


Hybrid Automatic Repeat Request-Acknowledgement
0, 16


(HARQ-ACK) bitmap



Uplink/Supplementary Uplink (UL/SUL) Indicator
0, 1


Bandwidth part indicator
0, 1, 2


Frequency domain resource assignment
Variable


Time domain resource assignment
0, 1, 2, 3, 



4, 5, or 6


Frequency Hopping Flag
0, 1


Modulation and coding scheme
5


New data indicator
1


Redundancy version
2


Hybrid Automatic Repeat Request (HARQ) process number
4


1st Downlink assignment index
1, 2, or 4


2nd Downlink assignment index
0, 2, or 4


TPC command for scheduled Physical Uplink Shared
2


Channel (PUSCH)



Sounding Reference Signal (SRS) resource indicator
Variable


Precoding information and number of layers (transmitted
0, 1, 2, 3, 


precoding matrix indicator (TPMI))
4, 5, 6


Antenna ports
2, 3, 4, 5


SRS request
2


Channel State Information (CSI) request
0, 1, 2, 3, 



4, 5, 6


Code Block Group (CBG) transmission information
0, 2, 4, 6, 8


(CBGTI)



Phase Tracking Reference Signal (PTRS) - Demodulation
0, 2


Reference Signal (DMRS) Association



beta_offsetr Indicator
0, 2


DMRS Sequence Initialization
0, 1


Uplink Shared Channel (UL-SCH) Indicator
1


ChannelAccess-CPext-CAPC
0, 1, 2, 3, 



4, 5 or 6


Open-loop power control parameter set indication
0 or 1 or 2 bits


Priority indicator
0, 1


Invalid symbol pattern indicator
0, 1


Minimum applicable scheduling offset indicator
0, 1


Secondary Cell (SCell) dormancy indication
0, 1, 2, 3, 4, 5


Sidelink assignment index
0, 1, 2








<br/>
[Table 4]

TABLE 4







DCI Format 1_1








Field
Bits





Identifier for Downlink Control Information (DCI) formats
1


Carrier indicator
0, 3


Bandwidth part indicator
0, 1, 2


Frequency domain resource assignment
Variable


Time domain resource assignment
0, 1, 2, 3, 4


Virtual Resource Block to Physical
0, 1


Resource Block (VRB-to-PRB) mapping



Physical Resource Block (PRB) bundling size indicator
0, 1


Rate matching indicator
0, 1, 2


ZP CSI-RS Trigger
0, 1, 2


Modulation and coding scheme [Transport Block 1 (TB1)]
5


New data indicator [TB1]
1


Redundancy version [TB1]
2


Modulation and coding scheme [Transport Block 2 (TB2)]
5


New data indicator [TB2]
1


Redundancy version [TB2]
2


Hybrid Automatic Repeat Request (HARQ) 
4


process number



Downlink assignment index
0, 2, 4, 6


TPC command for scheduled Physical Uplink Shared 
2


Channel (PUCCH)



PUCCH resource indicator
3


Physical Uplink Shared Channel to Hybrid 
0, 1, 2, 3


Automatic Repeat Request feedback 



(PDSCH-to-HARQ_feedback) timing indicator



One-shot HARQ-ACK request
0, 1


PDSCH group index
0, 1


New feedback indicator
0, 1, 2


Number of requested PDSCH group(s)
0, 1


Antenna port(s) and number of layers
4, 5, 6


Transmission configuration indication
0, 3


Sounding Reference Signal (SRS) request
2


Code Block Group (CBG) transmission 
0, 2, 4, 6, 8


information (CBGTI)



CBG flushing out information (CBGFI)
0, 1


Demodulation Reference Signal (DMRS) sequence 
1


initialization



DMRS Sequence Initialization
0, 1


Priority indicator
0, 1


ChannelAccess-CPext-CAPC
0, 1, 2, 3, 4


Minimum applicable scheduling offset indicator
0, 1


Secondary Cell (SCell) dormancy indication
0, 1, 2, 3, 4, 



5

In this example, a field (e.g., CBGTI field or other appropriate field) of the DCI <b>710</b> may be in the form of a bitmap having a separate bit representing the ON/OFF configuration for each CORESET and/or each search space set that the UE <b>3</b> that the UE <b>3</b> may be configured with (e.g., where ‘1’ indicates ‘ON’; ‘0’ indicates ‘OFF’ or vice versa). The mapping of each bit of the DCI field to a specific CORESET (and hence the associated search space(s) configured for that CORESET) may be based on the CORESET identifier/index (e.g., the controlResourceSetId IE) with each bit representing a different configured CORESET in ascending (or descending) order of CORESET identifier.

The mapping of each bit of the field of the DCI <b>710</b> to a specific search space set (or group of search space sets) may be based on the search space (e.g., using a SearchSpaceID or the like), or a common search space group identifier/index (e.g., a searchSpaceGroupId or the like), with each bit representing a different configured search space set, or group of search space sets, in ascending (or descending) order of the identifier/index.

FIG. <b>8</b>B is a simplified timing diagram illustrating a procedure, which may be implemented in the telecommunication system <b>1</b> of FIG. <b>1</b>, and in which a field of DCI format 0_1 and/or DCI format 1_1 is used to provide a CORESET ON/OFF indication and/or a search space ON/OFF indication when the UE <b>3</b> is active (e.g., in a DRX ON period of a DRX cycle).

As seen in FIG. <b>8</b>B when the UE <b>3</b> operating in a DRX mode and is in an active state during the DRX ON period it monitors for control information in DCI format 0_1 and/or 1_1 at S<b>820</b>. When the base station <b>5</b> determines, at S<b>822</b>, that the UE <b>3</b> requires a CORESET and/or search space set reconfiguration, the base station <b>5</b> sends, at S<b>824</b>, downlink control information using DCI Format 0_1 and/or 1_1 with a field (e.g., CBGTI field or other appropriate field) set to provide the corresponding CORESET ON/OFF indication and/or a search space ON/OFF indication representing the new configuration.

The UE <b>3</b> reconfigures, at S<b>826</b>, its CORESET(s) and/or search space set(s) appropriately based on the content of the received DCI field.

The UE <b>3</b> may have its CORESET(s) and/or search space set(s) more than once while it is active by repeating the reconfiguration procedure as indicated in steps S<b>822</b>′ to S<b>824</b>′.

UE Assistance Information for reduced PDCCH monitoring A possible mechanism for using UE Assistance Information to facilitate reduced PDCCH monitoring will now be described in more detail, by way of example only, with reference to FIG. <b>9</b>.

FIG. <b>9</b> is a simplified timing diagram illustrating a procedure, which may be implemented in the telecommunication system <b>1</b> of FIG. <b>1</b> for a UE <b>3</b> to report its reduced PDCCH monitoring capability to the base station.

As seen in FIG. <b>9</b>, the UE stores a power saving preference table (or set of sub-tables) at S<b>912</b> that includes a number of discrete power saving configurations, this power saving table (or set of sub-tables) may be a preconfigured standardised table or may be configurable by the base station <b>5</b> using RRC signalling (as illustrated at S<b>910</b>) or system information (as illustrated at S<b>911</b>).

The UE power saving preference table defines a plurality of different UE power saving configurations, each power saving configuration representing different respective power saving assistance information comprising a set of characteristic parameters.

The UE power saving assistance information may include any suitable parameters relating to a UE's (e.g., a REDCAP UE's) configuration, power saving capabilities and/or constraints. For example, the power saving information will typically include configurable PDCCH monitoring parameters and search space configuration parameters (for each SCS), such as maximum number of blind decoding attempts and/or maximum number of PDCCH candidates per aggregation level. Moreover, since some devices may not support the usage of small aggregation levels information on the supported aggregation levels may also form part of the information representing a particular power saving configuration in the UE power saving preference table.

Whilst in release In Release 16, there could be up to 10 configured search space sets, the maximum number of configured search space sets may be reduced for REDCAP UEs. Furthermore, as described above, not all of the configured search space sets need to be monitored simultaneously for such UEs. For example, a REDCAP UE may support five configured search space sets, but only be able to monitor three search space sets at any one time. In order to support the reporting of such information the UE power saving preference table may also include the maximum number of configurable search space sets and/or the maximum number of simultaneously monitored search space sets in power saving assistance information for each power saving configuration.

The UE power saving assistance information may also provide use case scenario related information, such as expected UE battery life, reference bit rate, peak bit rate, latency.

An example format for a pair of sub-tables that may form the power saving preference information (or part of it), is provided below in Table 5 and Table 6. It will be appreciated that the exemplary tables are purely illustrative.

[Table 5]

TABLE 5







Example Power Saving Assistance Information 1


















Maximum



PDCCH


Max
Maximum
number of



monitoring


number
number of
simultaneously



and Search

Number of
of blind
configurable
monitored



Space
Aggregation
candidates/
decoding
search
search space



Config
level (s)
CCEs
attempts
space sets
sets
. . .





1








2








3








. . .
. . .
. . .
. . .
. . .
. . .
. . .


n








<br/>
[Table 6]

TABLE 6







Example Power Saving Assistance Information 2













Use








Case



UE




Asst

Peak 

battery




Info
Reference
bit

life 




Config
bit rate
rate
Latency
(range)
. . .
. . .





1








2








3








. . .
. . .
. . .
. . .
. . .
. . .
. . .


n

At appropriate junctures, such as following an RRC reconfiguration procedure as seen S<b>914</b> in FIG. <b>9</b>, the UE <b>3</b> provides, at S<b>916</b>, UE assistance information to the base station <b>5</b> that includes one or more indexes or similar identifier representing the power configuration corresponding to its reduced capabilities/use case. The identifier may, for example, be in the form of a respective index corresponding to the row of each table or sub-table the forms the power saving configuration.

Based on this information, the base station <b>5</b> can efficiently determine the appropriate parameters and configurations to use for configuring communication with the UE <b>3</b> at S<b>918</b>. For example, the base station can determine suitable PDCCH monitoring parameters, and appropriate configuration of periodicity and multiplexing options.

PDCCH Candidate Dropping

The various search space prioritisation schemes for determining the order in which search spaces should be monitored and/or when PDCCH candidates should be dropped will now be described in more detail with reference to FIGS. <b>10</b> to <b>12</b>.

USS Priority Cycling

FIG. <b>10</b> is a simplified flow diagram illustrating a procedure which may be performed by a UE <b>3</b>, in the telecommunication system <b>1</b> of FIG. <b>1</b>, for searching for control information in a plurality of search spaces using USS priority cycling based prioritisation scheme.

As seen in FIG. <b>10</b> at the start of a given PDCCH monitoring occasion in a particular slot, the search space to be searched is initially set to the highest priority unsearched search space at S<b>1010</b>. Typically, where there is a CSS to be searched, this will be the highest priority CSS. As indicated at S<b>1012</b>, the procedure continues with this highest priority unsearched search space as the current search space.

The UE <b>3</b> will proceed to perform channel estimation for the CCEs of each PDCCH candidate of the current search space at S<b>1014</b>, and then attempt to blind decode that PDCCH candidate at S<b>1016</b>, in turn as long as there is still another unsearched PDCCH candidate for the current search space at S<b>1018</b>.

When there is no longer an unsearched PDCCH candidate at S<b>1018</b> the UE <b>3</b> determines whether there are any more unsearched search space sets for the current slot at S<b>1020</b>. If an unsearched search space still exists at S<b>1020</b> then the UE <b>3</b> checks, at S<b>1022</b> if searching that search space will result in the maximum number of channel estimated CCEs and/or maximum number of blind decodes being exceeded at S<b>1022</b>. If searching can continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1022</b>, then the UE <b>3</b> sets the current search space to be searched to the next highest priority search space at S<b>1024</b>, before repeating the procedure for the new current search space from S<b>1012</b> to S<b>1024</b> until either all the search spaces have been searched at S<b>1020</b> or the searching cannot continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1022</b>.

In S<b>1024</b> the priority of the search spaces is determined in accordance with the following order:

    
    
        An unsearched CSS is deemed to have the highest priority, if an unsearched CSS exists for current slot.
        The USS with the highest priority at the start of the search process will have the deemed next highest priority. As described in more detail below, this highest priority USS may be any one of the unsearched USSs and changes from slot-to-slot.
        The USSs are then prioritised in order of ascending index from the most recently searched USS until the highest index USS has been searched.
        The USSs are then prioritised in order of ascending index from the lowest index USS (assuming this was not the highest priority USS and so has not been searched already).

If the searching cannot continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1022</b>, then the remaining PDCCH candidates are skipped and the highest USS priority is reassigned at S<b>1026</b>. Specifically, the highest USS priority is reassigned cyclically, to the USS having the next index, in ascending order, after the current highest priority USS. If the current highest priority USS has the highest index USS then the highest USS priority is reassigned to the USS having the lowest index.

Once the highest USS priority has been reassigned at S<b>1026</b>, or when the search spaces have all been searched at S<b>1020</b>, the UE <b>3</b> waits at S<b>1028</b> for the next slot of the current (or next) PDCCH monitoring occasion before repeating the procedure starting at S<b>1010</b>.

It will be appreciated that this represents just one example of how a USS priority cycling based prioritisation scheme may be used for determining the order in which search spaces should be monitored. It will also be appreciated that the reassignment of the highest priority USS at S<b>1026</b> may also take place, when the search spaces have all been searched at S<b>1020</b>, before waiting at S<b>1028</b> for the next slot of the current (or next) PDCCH monitoring occasion at S<b>1010</b>.

CSS/USS Shared PDDCH Candidates

FIG. <b>11</b> is a simplified flow diagram illustrating a procedure which may be performed by a UE <b>3</b>, in the telecommunication system <b>1</b> of FIG. <b>1</b>, for searching for control information in a plurality of search spaces using a shared PDCCH candidate prioritisation scheme.

In this example, the UE <b>3</b> may be preconfigured (or dynamically configured using RRC signalling or system information) with a parameter indicating how the maximum number of PDCCH candidates should be shared between CSSs and USSs. This may simply be an information element indicating of a fraction or percentage of the maximum number of PDCCH candidates that may be searched for CSSs (or USSs).

As seen in FIG. <b>11</b> at the start of a given PDCCH monitoring occasion in a particular slot, the search space to be searched is initially set to the highest priority unsearched search space at S<b>1110</b>. Typically, where there is a CSS to be searched, this will be the highest priority CSS. As indicated at S<b>1112</b>, the procedure continues with this highest priority unsearched search space as the current search space.

The UE <b>3</b> will proceed to perform channel estimation for the CCEs of each PDCCH candidate of the current search space at S<b>1114</b>, and then attempt to blind decode that PDCCH candidate at S<b>1116</b>, in turn as long as there is still another unsearched PDCCH candidate for the current search space at S<b>1118</b>.

When there is no longer an unsearched PDCCH candidate at S<b>1118</b> the UE <b>3</b> determines whether there are any more unsearched search space sets for the current slot at S<b>1120</b>. If an unsearched search space still exists at S<b>1120</b> then the UE <b>3</b> checks, at S<b>1122</b> if searching that search space will result in the maximum number of channel estimated CCEs and/or maximum number of blind decodes being exceeded at S<b>1122</b>. If searching can continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1122</b>, then the UE <b>3</b> sets the current search space to be searched to the next highest priority search space at S<b>1124</b>, before repeating the procedure for the new current search space from S<b>1112</b> to S<b>1124</b> until either all the search spaces have been searched at S<b>1120</b> or the searching cannot continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1122</b>.

In S<b>1124</b> the priority of the search spaces is determined in accordance with the following order:

    
    
        An unsearched CSS is deemed to have the highest priority, if an unsearched CSS exists for current slot and the share of the maximum blind decoding attempts configured for the CSS will not be exceeded by searching that CSS.
        If the maximum blind decoding attempts configured for the CSS will be exceeded by searching that CSS, then the USS with the lowest index is deemed to have the deemed next highest priority.
        The USSs are then prioritised in order of ascending index from the most recently searched USS until the highest index USS has been searched.
        If every USS has been searched then any unsearched CSS can be searched provided that doing so will not cause the maximum number of channel estimated CCEs and/or maximum number of blind decodes to be exceeded at S<b>1122</b>.

If the searching cannot continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1122</b>, then the remaining PDCCH candidates are skipped at S<b>1126</b>.

When the remaining PDCCH candidates are skipped at S<b>1126</b>, or if the search spaces have all been searched at S<b>1120</b>, the UE <b>3</b> waits at S<b>1128</b> for the next slot of the current (or next) PDCCH monitoring occasion before repeating the procedure starting at S<b>1110</b>.

It will be appreciated that this represents just one example of how a shared PDCCH candidate based prioritisation scheme may be used for determining the order in which search spaces should be monitored. It will also be appreciated that this could be used in conjunction with the reassignment of the highest priority USS from slot to slot as described with reference to FIG. <b>10</b>.

Partial Searching of a Search Space

FIG. <b>12</b> is a simplified flow diagram illustrating a procedure which may be performed by a UE <b>3</b>, in the telecommunication system <b>1</b> of FIG. <b>1</b>, for facilitating a partial search for control information in a search space (e.g., a USS).

As seen in FIG. <b>12</b> at the start of a given PDCCH monitoring occasion in a particular slot, the search space to be searched is initially set to the highest priority unsearched search space at S<b>1210</b>. Typically, where there is a CSS to be searched, this will be the highest priority CSS. As indicated at S<b>1212</b>, the procedure continues with this highest priority unsearched search space as the current search space.

The UE <b>3</b> will proceed to perform channel estimation for the CCEs of each PDCCH candidate of the current search space at S<b>1214</b>, and then attempt to blind decode that PDCCH candidate at S<b>1216</b>, in turn as long as there is still another unsearched PDCCH candidate for the current search space at S<b>1218</b> and the maximum number of channel estimated CCEs and/or maximum number of blind decodes has not been reached at S<b>1222</b>.

When there is no longer an unsearched PDCCH candidate at S<b>1218</b> the UE <b>3</b> determines whether there are any more unsearched search space sets for the current slot at S<b>1220</b>. If an unsearched search space still exists at S<b>1220</b> then the UE <b>3</b> sets the current search space to be searched to the next highest priority search space at S<b>1224</b>, before repeating the procedure for the new current search space from S<b>1212</b> to S<b>1224</b> until either all the search spaces have been searched at S<b>1220</b> or the searching cannot continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1222</b>.

In S<b>1224</b> the priority of the search spaces may be based on the standard rules in which CSSs are prioritised over USSs and USSs are prioritised in order of ascending USS index. Nevertheless, it will be appreciated that the procedure of FIG. <b>12</b> could be modified to incorporate the USS priority cycling approach in which the highest priority USS is reassigned from slot to slot as described with reference to FIG. <b>10</b>. It will also be appreciated that the procedure of FIG. <b>12</b> could be modified to incorporate the shared PDCCH candidate approach in which the PDCCH candidates are shared between CSSs and USSs as described with reference to FIG. <b>11</b>.

If the searching cannot continue without exceeding the maximum number of channel estimated CCEs and/or maximum number of blind decodes at S<b>1222</b>, then the remaining PDCCH candidates are skipped at S<b>1226</b> even if the current search space has not been fully searched.

When the remaining PDCCH candidates are skipped at S<b>1226</b>, or if the search spaces have all been searched at S<b>1220</b>, the UE <b>3</b> waits at S<b>1228</b> for the next slot of the current (or next) PDCCH monitoring occasion before repeating the procedure starting at S<b>1210</b>.

It will be appreciated that this represents just one example of how a partial search space searching mechanism may be implemented.

Discontinuous PDCCH Monitoring

The mechanism for discontinuous PDCCH monitoring will now be described by way of example only, with reference to FIG. <b>13</b> which illustrates PDCCH monitoring during monitoring opportunities for the telecommunication system <b>1</b> of FIG. <b>1</b>.

In order to know when to search for control information the UEs <b>3</b> are configured to determine a PDDCH monitoring occasion, typically comprising a plurality of slots, within which it should search for the control information. This starting slot of each monitoring occasion is determine based on a number of parameters configured by the base station <b>5</b> at the UE <b>3</b> (e.g., the parameters defining the search spaces). These parameter include: a PDDCH monitoring periodicity of k<sub>s </sub>slots; a PDDCH monitoring offset of o<sub>s </sub>slots; a PDDCH monitoring pattern indicating the first symbol(s) of a CORESET within a slot for POOCH monitoring; and a duration of T<sub>s </sub>(<k<sub>s</sub>) slots indicating a number of slots for which the search space set extends.

Specifically, for a given search space s, a PDDCH monitoring occasion is determined to exist within a given slot (of number N<sub>s,f</sub><sup>μ</sup>) of a given frame (of number n<sub>f</sub>) if (N<sub>f</sub>·N<sub>slot</sub><sup>frame,μ</sup>+N<sub>s,f</sub><sup>μ</sup>−o<sub>s</sub>)mod k<sub>s</sub>=0 (where N<sub>slot</sub><sup>frame,μ</sup> is a number of slots per frame for the current SCS configuration μ). The UE monitors PDDCH candidates for search space set s for T<sub>s </sub>consecutive slots, starting from the slot n<sup>μ</sup><sub>s,f</sub>, and does not monitor PDCCH candidates for search space set s for the next k<sub>s</sub>-T<sub>s </sub>consecutive slots.

As seen in FIG. <b>13</b>, in the telecommunication system <b>1</b>, the UEs <b>3</b> are configurable to be able to monitor one slot every G slots sot of the T<sub>s </sub>consecutive slots where G is a configurable ‘monitoring regularity’ parameter or the like for indicating the how often the slots of a monitoring occasion should be monitored.

As seen in FIG. <b>13</b>, the parameter G may be set to an integer value representing a number of slots selected from a set of integer values (e.g., G {1, 2, 4, . . . }). The second and each subsequent consecutive value, in ascending order, in the set of integer values may beneficially be double the preceding value. This beneficially allows the regularity with which the slots of a monitoring occasion are monitored to be scaled, based on the numerology μ in use, with higher G values generality being use for higher values of μ.

The parameter G may be implicitly configured based on the configured numerology or may be explicitly configure by the base station <b>5</b> using RHO signalling. For example, the parameter G may be implicitly linked to the numerology μ by means of a table, or mathematical function, which provides a mapping between each numerology μ and a corresponding value of the parameter G.

Whilst use of a configurable parameter such as G provides greater flexibility to modify the regularity with which slots are monitored for a PDCCH within a given monitoring occasion, the UEs <b>3</b> may be configurable either to monitor the slots consecutively, or to monitor every other slot of the T<sub>s </sub>consecutive slots.

Modifications and Alternatives

Detailed examples of various improvements have been described above. As those skilled in the art will appreciate, a number of modifications and alternatives can be made to the above examples whilst still benefiting from the inventions embodied therein.

For example, it will be appreciated that, whilst the new and beneficial features of the devices of the telecommunication network have been described, in particular, with reference to 5G/NR communication technology, the beneficial features may be implemented in the devices of a telecommunication system that uses other communication technologies such as, for example, other communication technologies developed as part of the 3GPP. For example, whilst the base station and UEs have been described as a 5G base station (gNB) and corresponding UEs it will be appreciated that the features described above may be applied to the RAN nodes (eNBs) and UEs that implement LTE/LTE-Advanced communication technology, or RAN nodes and UEs that implement other communications technologies developed using 3GPP derived communication technologies.

It will be appreciated that the various improvements described above have particular utility when implemented as appropriate in REDCAP UEs and in base stations and other apparatus for supporting REDCAP UEs. Nevertheless, the improvements may also be implemented in non-REDCAP UEs and related apparatus to provide similar benefits.

In the above examples, the base station uses a 3GPP radio communications (radio access) technology to communicate with the UE. However, any other radio communications technology (i.e., WLAN, Wi-Fi, WiMAX, Bluetooth, etc.) can be used between the base station and the UE in accordance with the above example embodiments. The above example embodiments are also applicable to ‘non-mobile’ or generally stationary user equipment.

In the above description, the UEs and the base station are described for ease of understanding as having a number of discrete functional components or modules. Whilst these modules may be provided in this way for certain applications, for example where an existing system has been modified to implement the invention, in other applications, for example in systems designed with the inventive features in mind from the outset, these modules may be built into the overall operating system or code and so these modules may not be discernible as discrete entities.

In the above example embodiments, a number of software modules were described. As those skilled in the art will appreciate, the software modules may be provided in compiled or un-compiled form and may be supplied to the base station, to the mobility management entity, or to the UE as a signal over a computer network, or on a recording medium. Further, the functionality performed by part or all of this software may be performed using one or more dedicated hardware circuits. However, the use of software modules is preferred as it facilitates the updating of the base station or the UE in order to update their functionalities.

Each controller may comprise any suitable form of processing circuitry including (but not limited to), for example: one or more hardware implemented computer processors; microprocessors; central processing units (CPUs); arithmetic logic units (ALUs); input/output (IO) circuits; internal memories/caches (program and/or data); processing registers; communication buses (e.g., control, data and/or address buses); direct memory access (DMA) functions; hardware or software implemented counters, pointers and/or timers; and/or the like. Various other modifications will be apparent to those skilled in the art and will not be described in further detail here.

The base station may comprise a ‘distributed’ base station having a central unit ‘CU’ and one or more separate distributed units (DUs).

The User Equipment (or “UE”, “mobile station”, “mobile device” or “wireless device”) in the present disclosure is an entity connected to a network via a wireless interface.

It should be noted that the present disclosure is not limited to a dedicated communication device, and can be applied to any device having a communication function as explained in the following paragraphs.

The terms “User Equipment” or “UE” (as the term is used by 3GPP), “mobile station”, “mobile device”, and “wireless device” are generally intended to be synonymous with one another, and include standalone mobile stations, such as terminals, cell phones, smart phones, tablets, cellular IoT devices, IoT devices, and machinery. It will be appreciated that the terms “mobile station” and “mobile device” also encompass devices that remain stationary for a long period of time.

A UE may, for example, be an item of equipment for production or manufacture and/or an item of energy related machinery (for example equipment or machinery such as: boilers; engines; turbines; solar panels; wind turbines; hydroelectric generators; thermal power generators; nuclear electricity generators; batteries; nuclear systems and/or associated equipment; heavy electrical machinery; pumps including vacuum pumps; compressors; fans; blowers; oil hydraulic equipment; pneumatic equipment; metal working machinery; manipulators; robots and/or their application systems; tools; molds or dies; rolls; conveying equipment; elevating equipment; materials handling equipment; textile machinery; sewing machines; printing and/or related machinery; paper converting machinery; chemical machinery; mining and/or construction machinery and/or related equipment; machinery and/or implements for agriculture, forestry and/or fisheries; safety and/or environment preservation equipment; tractors; precision bearings; chains; gears; power transmission equipment; lubricating equipment; valves; pipe fittings; and/or application systems for any of the previously mentioned equipment or machinery etc.).

A UE may, for example, be an item of transport equipment (for example transport equipment such as: rolling stocks; motor vehicles; motorcycles; bicycles; trains; buses; carts; rickshaws; ships and other watercraft; aircraft; rockets; satellites; drones; balloons etc.).

A UE may, for example, be an item of information and communication equipment (for example information and communication equipment such as: electronic computer and related equipment; communication and related equipment; electronic components etc.).

A UE may, for example, be a refrigerating machine, a refrigerating machine applied product, an item of trade and/or service industry equipment, a vending machine, an automatic service machine, an office machine or equipment, a consumer electronic and electronic appliance (for example a consumer electronic appliance such as: audio equipment; video equipment; a loud speaker; a radio; a television; a microwave oven; a rice cooker; a coffee machine; a dishwasher; a washing machine; a dryer; an electronic fan or related appliance; a cleaner etc.).

A UE may, for example, be an electrical application system or equipment (for example an electrical application system or equipment such as: an x-ray system; a particle accelerator; radio isotope equipment; sonic equipment; electromagnetic application equipment; electronic power application equipment etc.).

A UE may, for example, be an electronic lamp, a luminaire, a measuring instrument, an analyzer, a tester, or a surveying or sensing instrument (for example a surveying or sensing instrument such as: a smoke alarm; a human alarm sensor; a motion sensor; a wireless tag etc.), a watch or clock, a laboratory instrument, optical apparatus, medical equipment and/or system, a weapon, an item of cutlery, a hand tool, or the like.

A UE may, for example, be a wireless-equipped personal digital assistant or related equipment (such as a wireless card or module designed for attachment to or for insertion into another electronic device (for example a personal computer, electrical measuring machine)).

A UE may be a device or a part of a system that provides applications, services, and solutions described below, as to “internet of things (IoT)”, using a variety of wired and/or wireless communication technologies.

Internet of Things devices (or “things”) may be equipped with appropriate electronics, software, sensors, network connectivity, and/or the like, which enable these devices to collect and exchange data with each other and with other communication devices. IoT devices may comprise automated equipment that follow software instructions stored in an internal memory. IoT devices may operate without requiring human supervision or interaction. IoT devices might also remain stationary and/or inactive for a long period of time. IoT devices may be implemented as a part of a (generally) stationary apparatus. IoT devices may also be embedded in non-stationary apparatus (e.g., vehicles) or attached to animals or persons to be monitored/tracked.

It will be appreciated that IoT technology can be implemented on any communication devices that can connect to a communications network for sending/receiving data, regardless of whether such communication devices are controlled by human input or software instructions stored in memory.

It will be appreciated that IoT devices are sometimes also referred to as Machine-Type Communication (MTC) devices or Machine-to-Machine (M2M) communication devices. It will be appreciated that a UE may support one or more IoT or MTC applications. Some examples of MTC applications are listed in the following table. This list is not exhaustive and is intended to be indicative of some examples of machine-type communication applications.

TABLE 7





Service Area
MTC applications







Security
Surveillance systems



Backup for landline



Control of physical access (e.g., to buildings)



Car/driver security


Tracking & Tracing
Fleet Management



Order Management



Pay as you drive



Asset Tracking



Navigation



Traffic information



Road tolling



Road traffic optimisation/steering


Payment
Point of sales



Vending machines



Gaming machines


Health
Monitoring vital signs



Supporting the aged or handicapped



Web Access Telemedicine points



Remote diagnostics


Remote 
Sensors


Maintenance/
Lighting


Control
Pumps



Valves



Elevator control



Vending machine control



Vehicle diagnostics


Metering
Power



Gas



Water



Heating



Grid control



Industrial metering


Consumer Devices
Digital photo frame



Digital camera



eBook

Applications, services, and solutions may be an MVNO (Mobile Virtual Network Operator) service, an emergency radio communication system, a PBX (Private Branch eXchange) system, a PHS/Digital Cordless Telecommunications system, a POS (Point of sale) system, an advertise calling system, an MBMS (Multimedia Broadcast and Multicast Service), a V2X (Vehicle to Everything) system, a train radio system, a location related service, a Disaster/Emergency Wireless Communication Service, a community service, a video streaming service, a femto cell application service, a VoLTE (Voice over LTE) service, a charging service, a radio on demand service, a roaming service, an activity monitoring service, a telecom carrier/communication NW selection service, a functional restriction service, a PoC (Proof of Concept) service, a personal information management service, an ad-hoc network/DTN (Delay Tolerant Networking) service, etc.

Further, the above-described UE categories are merely examples of applications of the technical ideas and exemplary embodiments described in the present document. Needless to say, these technical ideas and example embodiments are not limited to the above-described UE and various modifications can be made thereto.

Various other modifications will be apparent to those skilled in the art and will not be described in further detail here.

(Supplementary Note 1)

A method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising:

    
    
        receiving, from the radio access network, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information;
        monitoring for downlink control information (DCI) transmitted by the radio access network within the at least one search space within the at least one set of control resources;
        receiving, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information; and
        monitoring for DCI transmitted by the radio access network within the at least one search space within the set of control resources as reconfigured by the third information;
        wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.
<br/>
(Supplementary Note 2)

A method as noted in supplementary note 1 wherein the indication the third information comprises a bitmap wherein each bit of the bitmap represents a respective set of control resources configured by the first information or at least one respective search space configured by the second information, optionally where a bit of a bitmap is set to ‘0’ to indicate that the UE is to stop monitoring for DCI, and to ‘1’ to indicate that the UE is start monitoring for DCI, or continue monitoring for DCI.

(Supplementary Note 3)

A method as noted in supplementary note 1 or 2 wherein the UE is operating in a discontinuous reception (DRX) mode and receives the third information during whilst in an inactive state during a DRX cycle.

(Supplementary Note 4)

A method as noted in supplementary note 3 wherein the UE receives the third information, whilst in an inactive state during an OFF period of the DRX cycle, in a field of a DCI format that is receivable during the OFF period of the DRX cycle.

(Supplementary Note 5)

A method as noted in supplementary note 4 wherein the third information is received in a field of DCI format 2_6, optionally a wake-up signal (WUS) field of DCI format 2_6.

(Supplementary Note 6)

A method as noted in supplementary note 3 wherein the UE receives the third information during whilst in an inactive state during an ON period of the DRX cycle.

(Supplementary Note 7) A method as noted in supplementary note 3 or 6 wherein the third information is received in a field of DCI format 0_1 or DCI format 1_1, optionally a code block group (CBG) transmission information (CBGTI) field of DCI format 0_1 or DCI format 1_1.
<br/>
(Supplementary Note 8)

A method as noted in any of supplementary notes 1 to 7 wherein the UE stores information identifying a maximum number of search space sets that can be simultaneously monitored by the UE, wherein the information is configurable to any of a plurality of different values.

(Supplementary Note 9)

A method as noted in any of supplementary notes 1 to 8 wherein the first information for configuring at least one set of resources for receiving and/or the second information for configuring at least one is received using radio resource control (RRC) signalling.

(Supplementary Note 10)

A method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising:

    
    
        obtaining information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration; and
        providing, to the radio access network, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE.
<br/>
(Supplementary Note 11)

A method as noted in supplementary note 10 wherein the information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration respectively comprises at least one index representing each power saving configuration, and wherein the indication of at least one power saving configuration comprises the respective at least one index corresponding to each of the at least one power saving configuration.

(Supplementary Note 12)

A method as noted in supplementary note 10 or 11, wherein the information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration comprises at least one table.

(Supplementary Note 13)

A method as noted in any of supplementary notes 10 to 12, wherein the set of parameters that characterise that power configuration comprises at least one parameter from the following list of parameters: at least one parameter for use in configuring a search space; at least one parameter for use in configuring a monitoring occasion within which the UE is to monitor for control information; at least one parameter indicating a maximum number of blind decoding attempts supported by the UE; at least one parameter indicating a maximum number of physical downlink control channel (PDCCH) candidates per aggregation level supported at the UE; at least one parameter indicating a maximum number of control channel elements (CCEs) for channel estimation supported at the UE; at least one parameter indicating a corresponding aggregation level supported at the UE; at least one parameter indicating a maximum number of configurable search space sets supported at the UE; at least one parameter indicating a maximum number of simultaneously monitored search space sets supported at the UE; at least one parameter representing an expected UE battery life; at least one parameter representing a reference bit rate requirement for the UE; at least one parameter representing a peak bit rate requirement for the UE; and at least one parameter representing a latency requirement for the UE.

(Supplementary Note 14)

A method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising:

    
    
        monitoring, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources;
        wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI;
        wherein the monitoring comprises, during a current slot of the monitoring occasion:
        
            (a) treating a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempting to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered;
            (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, selecting a remaining search space that has not been searched in the current slot to be searched next and repeating steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and
            (c) when an end to searching in the current slot is triggered, repeating steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered;
        
        
        wherein, before performing step (b), at least one USS is assigned to be a highest priority USS for the current slot;
        wherein, when selecting a search space to be searched next in step (b) the UE prioritises the remaining search spaces that have not been searched in the current slot based on based on a prioritisation scheme that requires that USSs are prioritised starting from a USS having a highest priority; and
        wherein the method further comprises, before repeating steps (a) to (c) during a subsequent slot of the monitoring occasion, reassigning a different USS to be highest priority USS.
<br/>
(Supplementary Note 15)

A method as noted in supplementary note 14 wherein, when selecting a search space to be searched next in step (b), after prioritising USS having a highest priority, the USSs are prioritised in ascending order of USS index until the USS having the highest USS index is reached, and then in ascending order of USS index from the USS having the lowest USS index if not already searched in the current slot.

(Supplementary Note 16)

A method as noted in supplementary note 14 or 15 wherein, when reassigning a different USS to be the highest priority USS, the UE: reassigns the highest priority to the USS that has the next USS index, in ascending order, to the USS index of the current highest priority USS when a higher index USS has not been searched in the current slot; and reassigns the highest priority to the USS to the USS having the lowest USS index, if not already searched in the current slot, when the current highest priority USS is the highest index USS.

(Supplementary Note 17)

A method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising:

    
    
        monitoring, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources;
        wherein the set of control resources comprise at least one control channel element (CCE) and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI, each PDCCH candidate comprising at least one CCE;
        wherein the monitoring comprises, during a current slot of the monitoring occasion:
        
            (a) treating a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempting to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered;
            (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, selecting a remaining search space that has not been searched in the current slot to be searched next and repeating steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and
            (c) when an end to searching in the current slot is triggered, repeating steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered;
        
        
        wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues;
        wherein, the UE is configured with a maximum share of the maximum number of blind decode attempts that can be used for searching CSSs; and
        wherein, when selecting a search space to be searched next in step (b) the UE prioritises the remaining search spaces that have not been searched in the current slot based on a prioritisation scheme that requires that CSSs that have not been searched in the current slot are prioritised until further searching in a CSS will cause the maximum share of the maximum number of blind decode attempts to be exceeded, after which USSs that have not been searched in the current slot are prioritised.
<br/>
(Supplementary Note 18)

A method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising:

    
    
        monitoring, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources;
        wherein the set of control resources comprise at least one control channel element (CCE) and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI, each PDCCH candidate comprising at least one CCE;
        wherein the monitoring comprises, during a current slot of the monitoring occasion:
        
            (a) treating a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempting to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered;
            (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, selecting a remaining search space that has not been searched in the current slot to be searched next and repeating steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and
            (c) when an end to searching in the current slot is triggered, repeating steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered; wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current search space and the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues, even when the current search space has not been fully searched.
<br/>
(Supplementary Note 19)

A method performed by a user equipment (UE) that communicates with a radio access network in a communication system, the method comprising:

    
    
        identifying a sequence of consecutive slots for forming a monitoring occasion; and
        monitoring, during the monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, within at least one set of control resources;
        wherein, when performing the monitoring, the UE monitors for control information in slots of the sequence of consecutive slots that are spaced apart by an unmonitored interval of at least one other slot of the sequence of consecutive slots.
<br/>
(Supplementary Note 20)

A method as noted in supplementary note 19 wherein the communication system has a plurality of different numerologies that can be used for communication, each numerology having a different respective subcarrier spacing and slot length, and wherein the unmonitored interval is determined based on at least one configuration parameter that is determined based on the numerology of the communications system that is being used for communication.

(Supplementary Note 21)

A user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to control the transceiver to:
        
            receive, from the radio access network, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information;
            monitor for downlink control information (DCI) transmitted by the radio access network within the at least one search space within the at least one set of control resources;
            receive, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information; and
            monitor for DCI transmitted by the radio access network within the at least one search space within the set of control resources as reconfigured by the third information;
        
        
        wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.
<br/>
(Supplementary Note 22)

A user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising:

    
    
        a controller and a transceiver, wherein the controller is configured:
        
            to obtain information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration; and
            to control the transceiver to provide, to the radio access network, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE.
<br/>
(Supplementary Note 23)

A user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to control the transceiver to:
        
            monitor, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources;
        
        
        wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI;
        wherein the controller is configured to control the UE, during a current slot of the monitoring occasion, to:
        
            (a) treat a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempt to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered;
            (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, select a remaining search space that has not been searched in the current slot to be searched next and repeat steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and
            (c) when an end to searching in the current slot is triggered, repeat steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered;
        
        
        wherein, before performing step (b), at least one USS is assigned to be a highest priority USS for the current slot;
        wherein the controller is configured to control the UE to, when selecting a search space to be searched next in step (b), prioritise the remaining search spaces that have not been searched in the current slot based on based on a prioritisation scheme that requires that USSs are prioritised starting from a USS having a highest priority; and
        wherein the controller is configured to control the UE to, before repeating steps (a) to (c) during a subsequent slot of the monitoring occasion, reassign a different USS to be highest priority USS.
<br/>
(Supplementary Note 24)

A user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to control the transceiver to:
        
            monitor, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources;
        
        
        wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI;
        wherein the controller is configured to control the UE, during a current slot of the monitoring occasion, to:
        
            (a) treat a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempt to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered;
            (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, select a remaining search space that has not been searched in the current slot to be searched next and repeat steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and
            (c) when an end to searching in the current slot is triggered, repeat steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered;
        
        
        wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues;
        wherein, the UE is configured with a maximum share of the maximum number of blind decode attempts that can be used for searching CSSs; and
        wherein the controller is configured to control the UE to, when selecting a search space to be searched next in step (b), UE prioritise the remaining search spaces that have not been searched in the current slot based on a prioritisation scheme that requires that CSSs that have not been searched in the current slot are prioritised until further searching in a CSS will cause the maximum share of the maximum number of blind decode attempts to be exceeded, after which USSs that have not been searched in the current slot are prioritised.
<br/>
(Supplementary Note 25)

A user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to control the transceiver to:
        
            monitor, during a monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, comprising at least one common search space (CSS) and at least on UE specific search space (USS), within at least one set of control resources;
        
        
        wherein the set of control resources comprise at least one control channel element and each search space comprises a respective set of physical downlink control channel (PDCCH) candidates within which to search for DCI;
        wherein the controller is configured to control the UE, during a current slot of the monitoring occasion, to:
        
            (a) treat a first search space of the plurality of search spaces that has not been searched in the current slot as a current search space and attempt to blind decode each PDCCH candidate of the current search space in turn until an end to searching of the current search space is triggered;
            (b) when the current search space has been fully searched, and the plurality of search spaces include at least one remaining search space that has not been searched in the current slot, select a remaining search space that has not been searched in the current slot to be searched next and repeat steps (a) and (b) with the selected search space as the current search space, unless an end to searching in the current slot is triggered; and
            (c) when an end to searching in the current slot is triggered, repeat steps (a) to (c) during a subsequent slot of a monitoring occasion as the current slot, until an end to searching in the monitoring occasion is triggered;
        
        
        wherein, the UE is configured with a maximum number of blind decode attempts, and an end to searching in the current search space and the current slot is triggered when the maximum number of blind decode attempts will be exceeded if searching continues, even when the current search space has not been fully searched.
<br/>
(Supplementary Note 26)

A user equipment (UE) for communicating with a radio access network in a communication system, the UE comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to identify a sequence of consecutive slots for forming a monitoring occasion, and to control the transceiver to monitor, during the monitoring occasion, for downlink control information (DCI) transmitted by the radio access network within a plurality of search spaces, within at least one set of control resources;
        wherein the controller is configured to control the UE to monitor for control information in slots of the sequence of consecutive slots that are spaced apart by an unmonitored interval of at least one other slot of the sequence of consecutive slots.
<br/>
(Supplementary Note 27)

A method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising:

    
    
        transmitting, to the UE, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information; and
        transmitting, to the UE, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information;
        wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.
<br/>
(Supplementary Note 28)

A method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising:

    
    
        obtaining information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration;
        receiving, from the UE, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE; and
        configuring communication with the UE based on the received UE assistance information.
<br/>
(Supplementary Note 29)

A method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising:

    
    
        transmitting, to the UE, information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring a plurality of search spaces, comprising at least on UE specific search space (USS), within at least one set of control resources, wherein the information comprises information for configuring a maximum share of a maximum number of blind decode attempts that can be used by the UE for searching a common search space (CSSs).
<br/>
(Supplementary Note 30)

A method performed by a radio access network that communicates with a user equipment (UE) in a communication system, the method comprising:

    
    
        transmitting, to the UE, information indicating a sequence of consecutive slots for forming a monitoring occasion, wherein the information comprises information for indicating an interval between slots of the sequence of consecutive slots that is to remain unmonitored by the UE.
<br/>
(Supplementary Note 31)

A radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to control the transceiver to:
        transmit, to the UE, first information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring at least one search space within the set of control resources within which to search for control information; and
        transmit, to the UE, from the radio access network, DCI comprising third information for reconfiguring the at least one set of control resources configured by the first information, or the at least one search space configured by the second information;
        wherein the third information is configured to provide an indication of at least one set of control resources configured by the first information, or of at least one search space configured by the second information, within which the UE is to stop monitoring for DCI, start monitoring for DCI, or continue monitoring for DCI.
<br/>
(Supplementary Note 32)

A radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising:

    
    
        a controller and a transceiver, wherein the controller is configured: to obtain information for mapping each of a plurality of possible power saving configurations to a set of parameters that characterise that power configuration; to control the transceiver to receive, from the UE, UE assistance information comprising an indication of at least one power saving configuration, of the plurality of power saving configurations, that represents a configuration or capability of the UE; and to configure communication with the UE based on the received UE assistance information.
<br/>
(Supplementary Note 33)

A radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to control the transceiver to transmit, to the UE, information for configuring at least one set of control resources in which the radio access network may transmit control information, and second information for configuring a plurality of search spaces, comprising at least on UE specific search space (USS), within at least one set of control resources, wherein the information comprises information for configuring a maximum share of a maximum number of blind decode attempts that can be used by the UE for searching a common search space (CSSs).
<br/>
(Supplementary Note 34)

A radio access network node for communicating with a user equipment (UE) in a communication system, the radio access network node comprising:

    
    
        a controller and a transceiver, wherein the controller is configured to control the transceiver to transmit, to the UE, information indicating a sequence of consecutive slots for forming a monitoring occasion, wherein the information comprises information for indicating an interval between slots of the sequence of consecutive slots that is to remain unmonitored by the UE.

This application is based upon and claims the benefit of priority from United Kingdom Patent Application No. 2012353.5, filed on Aug. 7, 2020, the disclosure of which is incorporated herein in its entirety by reference.

## Claims

1. A method performed by a user equipment (UE), the method comprising:
receiving, from an access network node, a Radio Resource Control (RRC) message including information indicating:
a slot unit G as a power of two;
a duration of consecutive slots T<sub>s</sub>; and
a monitoring periodicity k<sub>s </sub>including the duration T<sub>s </sub>and an unmonitoring duration k<sub>s</sub>-T<sub>s</sub>; and

monitoring a physical downlink control channel at monitoring slots determined per G slots during the consecutive slots T<sub>s </sub>of the duration.

2. The method according to claim 1, wherein the G corresponds to one of a plurality of numerologies that is being used for communication of the UE.

3. The method according to claim 1, wherein the higher G corresponds to the higher numerology.

4. Δ user equipment (UE), comprising:
a memory storing instructions; and
at least one processor configured to process the instructions to:
receive, from an access network node, a Radio Resource Control (RRC) message including information indicating:
a slot unit G as a power of two;
a duration of consecutive slots T<sub>s</sub>; and
a monitoring periodicity k<sub>s </sub>including the duration T<sub>s </sub>and an unmonitoring duration k<sub>s</sub>-T<sub>s</sub>; and
monitor a physical downlink control channel at monitoring slots determined per G slots during the consecutive slots T<sub>s </sub>of the duration.

5. The UE according to claim 4, wherein the G corresponds to one of a plurality of numerologies that is being used for communication of the UE.

6. The UE according to claim 5, wherein the higher G corresponds to the higher numerology.

7. A method performed by an access network node, the method comprising:
transmitting, to a user equipment (UE), a Radio Resource Control (RRC) message including information indicating:
a slot unit G as a power of two;
a duration of consecutive slots T<sub>s</sub>; and
a monitoring periodicity k<sub>s </sub>including the duration T<sub>s </sub>and an unmonitoring duration k<sub>s</sub>-T<sub>s</sub>; and

transmitting a physical downlink control channel at monitoring slots determined per G slots during the consecutive slots T<sub>s </sub>of the duration.

8. A radio access network node comprising:
a memory storing instructions; and
at least one processor configured to process the instructions to:
transmit, to a user equipment (UE), a Radio Resource Control (RRC) message including information indicating:
a slot unit G as a power of two;
a duration of consecutive slots T<sub>s</sub>;
a monitoring periodicity k<sub>s </sub>including the duration T<sub>s </sub>and an unmonitoring duration k<sub>s</sub>-T<sub>s</sub>; and

transmit a physical downlink control channel at monitoring slots determined per G slots during the consecutive slots T<sub>s </sub>of the duration.

