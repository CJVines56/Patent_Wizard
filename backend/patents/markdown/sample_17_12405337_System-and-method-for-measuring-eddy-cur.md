# System and method for measuring eddy currents with long time constants using a pseudo-continuous acquisition (Doc 12405337)

- Doc ID: 12405337
- Title: System and method for measuring eddy currents with long time constants using a pseudo-continuous acquisition
- Filing Date: 20231005
- Classification: G01R 33/58
- Authors: Richard Scott Hinks; Andreas Ebel; Hua Li

## Abstract

A system and a method for measuring eddy currents with long time constants includes initiating, via a processor, a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner. The system and the method also include utilizing, via the processor, a train of gradient echo sequences to simultaneously generate and measure the eddy currents during the calibration scan. Both eddy current generation and measurement are completed within each gradient echo sequence of the train of gradient echo sequences. The system and the method further include acquiring, via the processor, k-space data from the train of gradient echo sequences. The system and the method still further include converting, via the processor, the k-space data to eddy current gradient fields. The system and the method even further include estimating, via the processor, the eddy currents as a function of time based on the eddy current gradient fields.

## Description

The subject matter disclosed herein relates to medical imaging and, more particularly, to a system and a method for measuring eddy currents with long time constants using a pseudo-continuous acquisition.

Non-invasive imaging technologies allow images of the internal structures or features of a patient/object to be obtained without performing an invasive procedure on the patient/object. In particular, such non-invasive imaging technologies rely on various physical principles (such as the differential transmission of X-rays through a target volume, the reflection of acoustic waves within the volume, the paramagnetic properties of different tissues and materials within the volume, the breakdown of targeted radionuclides within the body, and so forth) to acquire data and to construct images or otherwise represent the observed internal features of the patient/object.

During MRI, when a substance such as human tissue is subjected to a uniform magnetic field (polarizing field B<sub>0</sub>), the individual magnetic moments of the spins in the tissue attempt to align with this polarizing field, but precess about it in random order at their characteristic Larmor frequency. If the substance, or tissue, is subjected to a magnetic field (excitation field B<sub>1</sub>) which is in the x-y plane and which is near the Larmor frequency, the net aligned moment, or “longitudinal magnetization”, M<sub>z</sub>, may be rotated, or “tipped”, into the x-y plane to produce a net transverse magnetic moment, M<sub>t</sub>. A signal is emitted by the excited spins after the excitation signal B<sub>1 </sub>is terminated and this signal may be received and processed to form an image.

When utilizing these signals to produce images, magnetic field gradients (G<sub>x</sub>, G<sub>y</sub>, and G<sub>z</sub>) are employed. Typically, the region to be imaged is scanned by a sequence of measurement cycles in which these gradient fields vary according to the particular localization method being used. The resulting set of received nuclear magnetic resonance (NMR) signals are digitized and processed to reconstruct the image using one of many well-known reconstruction techniques.

In MRI, eddy currents are un-wanted electrical currents generated in metallic structures within the MRI system when the gradient field changes. The magnetic fields associated with eddy currents distort the ideal gradient waveforms and cause artifacts in MRI images. The eddy currents can commonly be characterized by a number of exponential terms and oscillatory terms. Exponential terms are the dominant terms. During installation of an MRI system, eddy currents are measured (e.g., during system calibration). Usually an MRI sequence (e.g., setting of pulse sequences and pulsed field gradients) for measuring eddy currents involve two main steps. The first main step includes initiating the eddy current fields by applying an excitation gradient pulse. The second main step includes utilizing multiple RF pulses to measure the time-dependent eddy current fields. However, this approach has limitations. Typically, the duration of the excitation gradient is much longer than the eddy current time constant (e.g., with durations of approximately 45 seconds for very long time constants (e.g., in the order of 10 seconds)). This prolonged gradient duration leads to inefficiency in data collection since no data is acquired during the excitation gradient pulse. Additionally, the extended gradient duration introduces vulnerability to magnet drift effects such as movement of metal (e.g., due to ferromagnetic material in the local area) or B<sub>0 </sub>drift of the main magnetic field.

A summary of certain embodiments disclosed herein is set forth below. It should be understood that these aspects are presented merely to provide the reader with a brief summary of these certain embodiments and that these aspects are not intended to limit the scope of this disclosure. Indeed, this disclosure may encompass a variety of aspects that may not be set forth below.

In one embodiment, a computer-implemented method for measuring eddy currents with long time constants is provided. The computer-implemented method includes initiating, via a processor, a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner. The computer-implemented method also includes utilizing, via the processor, a train of gradient echo sequences to simultaneously generate and measure the eddy currents during the calibration scan, wherein both eddy current generation and measurement are completed within each gradient echo sequence. The computer-implemented method further includes acquiring, via the processor, k-space data from the train of gradient echo sequences. The computer-implemented method still further includes converting, via the processor, the k-space data to eddy current gradient fields. The computer-implemented method even further includes estimating, via the processor, the eddy currents as a function of time based on the eddy current gradient fields.

In another embodiment, a system for measuring eddy currents with long time constants is provided. The system includes a memory encoding processor-executable routines. The system also includes a processor configured to access the memory and to execute the processor-executable routines, wherein the processor-executable routines, when executed by the processor, cause the processor to perform actions. The actions include initiating a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner. The actions also include utilizing a train of gradient echo sequences to simultaneously generate and measure the eddy currents during the calibration scan, wherein both eddy current generation and measurement are completed within each gradient echo sequence of the train of gradient echo sequences. The actions further include acquiring k-space data from the train of gradient echo sequences. The actions still further include converting the k-space data to eddy current gradient fields. The actions even further include estimating the eddy currents as a function of time based on the eddy current gradient fields.

In a further embodiment, a non-transitory computer-readable medium, the non-transitory computer-readable medium including processor-executable code that when executed by a processor, causes the processor to perform actions. The actions include initiating a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner. The actions also include utilizing a train of gradient echo sequences to simultaneously generate and measure the eddy currents during the calibration scan, wherein both eddy current generation and measurement are completed within each gradient echo sequence of the train of gradient echo sequences. The actions further include acquiring k-space data from the train of gradient echo sequences. The actions still further include converting the k-space data to eddy current gradient fields. The actions even further include estimating the eddy currents as a function of time based on the eddy current gradient fields.

These and other features, aspects, and advantages of the present subject matter will become better understood when the following detailed description is read with reference to the accompanying drawings in which like characters represent like parts throughout the drawings, wherein:

FIG. <b>1</b> illustrates a schematic diagram of an embodiment of a magnetic resonance imaging (MRI) system suitable for use with the disclosed technique;

FIG. <b>2</b> illustrates a pulse sequence diagram for a gradient echo sequence utilized to measure eddy currents with long time constants (e.g., having eddy current excitation gradients with positive polarity), in accordance with aspects of the present disclosure;

FIG. <b>3</b> illustrates a pulse sequence diagram for a gradient echo sequence utilized to measure eddy currents with long time constants (e.g., having eddy current excitation gradients with negative polarity), in accordance with aspects of the present disclosure;

FIG. <b>4</b> illustrates a pulse sequence diagram for a gradient echo sequence utilized to measure eddy currents with long time constants (e.g., lacking eddy current excitation gradients), in accordance with aspects of the present disclosure;

FIG. <b>5</b> illustrates a flow chart of a method for measuring eddy currents with long time constants, in accordance with aspects of the present disclosure;

FIG. <b>6</b> is a graph illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 0.01 seconds and an amplitude −0.1%) as part of a test procedure, in accordance with aspects of the present disclosure;

FIG. <b>7</b> is a graph illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 0.1 seconds and an amplitude −0.1%) as part of a test procedure, in accordance with aspects of the present disclosure;

FIG. <b>8</b> is a graph illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 1.0 second and an amplitude −0.1%) as part of a test procedure, in accordance with aspects of the present disclosure;

FIG. <b>9</b> is a graph illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 10 seconds and an amplitude −0.1%) as part of a test procedure, in accordance with aspects of the present disclosure; and

FIG. <b>10</b> illustrates a pulse sequence diagram for a free induction decay sequence utilized to measure eddy currents with long time constants (e.g., having eddy current excitation gradients with positive polarity), in accordance with aspects of the present disclosure.

One or more specific embodiments will be described below. In an effort to provide a concise description of these embodiments, not all features of an actual implementation are described in the specification. It should be appreciated that in the development of any such actual implementation, as in any engineering or design project, numerous implementation-specific decisions must be made to achieve the developers' specific goals, such as compliance with system-related and business-related constraints, which may vary from one implementation to another. Moreover, it should be appreciated that such a development effort might be complex and time consuming, but would nevertheless be a routine undertaking of design, fabrication, and manufacture for those of ordinary skill having the benefit of this disclosure.

When introducing elements of various embodiments of the present subject matter, the articles “a,” “an,” “the,” and “said” are intended to mean that there are one or more of the elements. The terms “comprising,” “including,” and “having” are intended to be inclusive and mean that there may be additional elements other than the listed elements. Furthermore, any numerical examples in the following discussion are intended to be non-limiting, and thus additional numerical values, ranges, and percentages are within the scope of the disclosed embodiments.

The present disclosure provides systems and methods for measuring eddy currents with long time constants. In particular, the systems and methods are configured to utilize a gradient echo sequence to measure the eddy currents with the long time constants. The disclosed embodiments include initiating a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner. The disclosed embodiments also include utilizing a train of gradient echo sequences to simultaneously generate and measure the eddy currents during the calibration scan. In the context of this description, the term simultaneously indicates that both eddy current generation and measurement are completed within each gradient echo sequence of the train of gradient echo sequences. The disclosed embodiments further include acquiring k-space data from the train of gradient echo sequences. The disclosed embodiments still further include converting the k-space data to eddy current gradient fields. The disclosed embodiments even further include estimating the eddy currents as a function of time based on the eddy current gradient fields.

In certain embodiments, the estimated eddy currents have a time constant at least two times longer than a repetition time of each gradient echo sequence of the train of gradient echo sequences. In certain embodiments, the induced eddy current can be approximated as resulting from a constant gradient with a duration equal to the time repetition and an amplitude equivalent to an average gradient, wherein the average gradient is a total gradient area of a respective gradient echo sequence of the train of gradient echo sequences divided by the time repetition. In certain embodiments, estimating the eddy currents as a function of time includes scaling the eddy current gradient fields by an average gradient strength and fitting the scaled eddy current gradient fields as a function of time. In certain embodiments, estimating the eddy currents as a function of time includes utilizing Equation 1 described below.

In certain embodiments, a first portion of each gradient echo sequence of the train of gradient echo sequences includes a balanced gradient echo (e.g., with a zero gradient area) for eddy current measurement, wherein the balanced gradient echo has a balanced readout gradient and slice gradient to avoid inducing additional eddy current effects (e.g., from the readout gradient and the slice gradient). In certain embodiments, a second portion of a set of gradient echo sequences of the train of gradient echo sequences includes an eddy current excitation gradient (or eddy current generating gradient) for eddy current generation. In certain embodiments, the second portion of some gradient echo sequences of the set of gradient echo sequences includes a negative eddy current excitation gradient and the second portion of some gradient echo sequences of the set of gradient echo sequences includes a positive eddy current excitation gradient. The utilization of the bipolar (i.e., positive and negative) eddy current excitation gradients enables eddy currents to be distinguished from B<sub>0 </sub>drift since eddy currents change direction in response to the bipolar eddy current excitation gradients and generally B<sub>0 </sub>drift does not.

The disclosed embodiments enable the simultaneous generation and measurement of eddy currents. This enables a pseudo-continuous scan (with the train of GRE sequences intermittently repeated) to be utilized to measure eddy currents with long time constants that takes less time and is more efficient than previous techniques. In addition, the disclosed embodiments are less sensitive to magnetic drift. The disclosed embodiments also improve the accuracy of calibration for eddy currents with very long time constants. By increasing the accuracy of the calibration, image quality is improved in certain MR images.

With the preceding in mind, FIG. <b>1</b> a magnetic resonance imaging (MRI) system <b>100</b> is illustrated schematically as including a scanner <b>102</b>, scanner control circuitry <b>104</b>, and system control circuitry <b>106</b>. According to the embodiments described herein, the MRI system <b>100</b> is generally configured to perform MR imaging.

System <b>100</b> additionally includes remote access and storage systems or devices such as picture archiving and communication systems (PACS) <b>108</b>, or other devices such as teleradiology equipment so that data acquired by the system <b>100</b> may be accessed on- or off-site. In this way, MR data may be acquired, followed by on- or off-site processing and evaluation. While the MRI system <b>100</b> may include any suitable scanner or detector, in the illustrated embodiment, the system <b>100</b> includes a full body scanner <b>102</b> having a housing <b>120</b> through which a bore <b>122</b> is formed. A table <b>124</b> is moveable into the bore <b>122</b> to permit a patient <b>126</b> (e.g., subject) to be positioned therein for imaging a selected anatomy within the patient.

Scanner <b>102</b> includes a series of associated coils for producing controlled magnetic fields for exciting the gyromagnetic material within the anatomy of the patient being imaged. Specifically, a primary magnet coil <b>128</b> is provided for generating a primary magnetic field, B<sub>0</sub>, which is generally aligned with the bore <b>122</b>. A series of gradient coils <b>130</b>, <b>132</b>, and <b>134</b> permit controlled magnetic gradient fields to be generated for positional encoding of certain gyromagnetic nuclei within the patient <b>126</b> during examination sequences. A radio frequency (RF) coil <b>136</b> (e.g., RF transmit coil) is configured to generate radio frequency pulses for exciting the certain gyromagnetic nuclei within the patient. In addition to the coils that may be local to the scanner <b>102</b>, the system <b>100</b> also includes a set of receiving coils or RF receiving coils <b>138</b> (e.g., an array of coils) configured for placement proximal (e.g., against) to the patient <b>126</b>. As an example, the receiving coils <b>138</b> can include cervical/thoracic/lumbar (CTL) coils, head coils, single-sided spine coils, and so forth. Generally, the receiving coils <b>138</b> are placed close to or on top of the patient <b>126</b> so as to receive the weak RF signals (weak relative to the transmitted pulses generated by the scanner coils) that are generated by certain gyromagnetic nuclei within the patient <b>126</b> as they return to their relaxed state.

The various coils of system <b>100</b> are controlled by external circuitry to generate the desired field and pulses, and to read emissions from the gyromagnetic material in a controlled manner. In the illustrated embodiment, a main power supply <b>140</b> provides power to the primary field coil <b>128</b> to generate the primary magnetic field, B<sub>0</sub>. A power input (e.g., power from a utility or grid), a power distribution unit (PDU), a power supply (PS), and a driver circuit <b>150</b> may together provide power to pulse the gradient field coils <b>130</b>, <b>132</b>, and <b>134</b>. The driver circuit <b>150</b> may include amplification and control circuitry for supplying current to the coils as defined by digitized pulse sequences output by the scanner control circuitry <b>104</b>.

Another control circuit <b>152</b> is provided for regulating operation of the RF coil <b>136</b>. Circuit <b>152</b> includes a switching device for alternating between the active and inactive modes of operation, wherein the RF coil <b>136</b> transmits and does not transmit signals, respectively. Circuit <b>152</b> also includes amplification circuitry configured to generate the RF pulses. Similarly, the receiving coils <b>138</b> are connected to switch <b>154</b>, which is capable of switching the receiving coils <b>138</b> between receiving and non-receiving modes. Thus, the receiving coils <b>138</b> resonate with the RF signals produced by relaxing gyromagnetic nuclei from within the patient <b>126</b> while in the receiving mode, and they do not resonate with RF energy from the transmitting coils (i.e., coil <b>136</b>) so as to prevent undesirable operation while in the non-receiving mode. Additionally, a receiving circuit <b>156</b> is configured to receive the data detected by the receiving coils <b>138</b> and may include one or more multiplexing and/or amplification circuits.

It should be noted that while the scanner <b>102</b> and the control/amplification circuitry described above are illustrated as being coupled by a single line, many such lines may be present in an actual instantiation. For example, separate lines may be used for control, data communication, power transmission, and so on. Further, suitable hardware may be disposed along each type of line for the proper handling of the data and current/voltage. Indeed, various filters, digitizers, and processors may be disposed between the scanner and either or both of the scanner and system control circuitry <b>104</b>, <b>106</b>.

As illustrated, scanner control circuitry <b>104</b> includes an interface circuit <b>158</b>, which outputs signals for driving the gradient field coils and the RF coil and for receiving the data representative of the magnetic resonance signals produced in examination sequences. The interface circuit <b>158</b> is coupled to a control and analysis circuit <b>160</b>. The control and analysis circuit <b>160</b> executes the commands for driving the circuit <b>150</b> and circuit <b>152</b> based on defined protocols selected via system control circuit <b>106</b>.

Control and analysis circuit <b>160</b> also serves to receive the magnetic resonance signals and performs subsequent processing before transmitting the data to system control circuit <b>106</b>. Scanner control circuit <b>104</b> also includes one or more memory circuits <b>162</b>, which store configuration parameters, pulse sequence descriptions, examination results, and so forth, during operation.

Interface circuit <b>164</b> is coupled to the control and analysis circuit <b>160</b> for exchanging data between scanner control circuitry <b>104</b> and system control circuitry <b>106</b>. In certain embodiments, the control and analysis circuit <b>160</b>, while illustrated as a single unit, may include one or more hardware devices. The system control circuit <b>106</b> includes an interface circuit <b>166</b>, which receives data from the scanner control circuitry <b>104</b> and transmits data and commands back to the scanner control circuitry <b>104</b>. The control and analysis circuit <b>168</b> may include a CPU in a multi-purpose or application specific computer or workstation. Control and analysis circuit <b>168</b> is coupled to a memory circuit <b>170</b> to store programming code for operation of the MRI system <b>100</b> and to store the processed image data for later reconstruction, display and transmission. The programming code may execute one or more algorithms that, when executed by a processor, are configured to perform reconstruction of acquired data as described below. In certain embodiments, the memory circuit <b>170</b> may store one or more neural networks for reconstruction of acquired data as described below. In certain embodiments, image reconstruction may occur on a separate computing device having processing circuitry and memory circuitry.

In certain embodiments, the programming code is configured to measuring eddy currents with long time constant. In particular, the programming code is configured to utilize an MRI sequence such as a gradient echo sequence to measure the eddy currents with the long time constant. The programming code is configured to initiate a calibration scan of a phantom utilizing an MRI scanner. The programming code is also configured to utilize a train of gradient echo sequences to repeatedly generate and measure the eddy currents in an interleaved fashion during the calibration scan. The programming code is further configured to acquire k-space data from the train of gradient echo sequences. The programming code is still further configured to convert the k-space data to eddy current gradient fields. The programming code is yet further configured to estimate the eddy currents as a function of time based on the eddy current gradient fields.

In certain embodiments, the estimated eddy currents have a time constant at least two times longer than a time repetition of each gradient echo sequence of the train of gradient echo sequences. In certain embodiments, the induced eddy current can be approximated as resulting from a constant gradient with a duration equal to the time repetition and an amplitude equivalent to an average gradient, wherein the average gradient is a total gradient area of a respective gradient echo sequence of the train of gradient echo sequences divided by the time repetition. In certain embodiments, the programming code is configured to estimate the eddy currents as a function of time by scaling the eddy current gradient fields by an average gradient strength and fitting the scaled eddy current gradient fields as a function of time. In certain embodiments, the programming code is configured to estimate the eddy currents as a function of time includes utilizing Equation 1 described below.

In certain embodiments, a first portion of each gradient echo sequence of the train of gradient echo sequences includes a balanced gradient echo (e.g., with a zero gradient area) for eddy current measurement, wherein the balanced gradient echo has a balanced readout gradient and slice gradient to avoid eddy current effect (e.g., from the readout gradient and the slice gradient). In certain embodiments, a second portion of a set of gradient echo sequences of the train of gradient echo sequences includes an eddy current excitation gradient (or eddy current generating gradient) for eddy current generation. In certain embodiments, the second portion of some gradient echo sequences of the set of gradient echo sequences includes a negative eddy current excitation gradient and the second portion of some gradient echo sequences of the set of gradient echo sequences includes a positive eddy current excitation gradient. The utilization of the bipolar (i.e., positive and negative) eddy current excitation gradients enables eddy currents to be distinguished from B<sub>0 </sub>drift since eddy currents change direction in response to the bipolar eddy current excitation gradients and B<sub>0 </sub>drift does not.

An additional interface circuit <b>172</b> may be provided for exchanging image data, configuration parameters, and so forth with external system components such as remote access and storage devices <b>108</b>. Finally, the system control and analysis circuit <b>168</b> may be communicatively coupled to various peripheral devices for facilitating operator interface and for producing hard copies of the reconstructed images. In the illustrated embodiment, these peripherals include a printer <b>174</b>, a monitor <b>176</b>, and user interface <b>178</b> including devices such as a keyboard, a mouse, a touchscreen (e.g., integrated with the monitor <b>176</b>), and so forth.

FIG. <b>2</b> illustrates a pulse sequence diagram <b>180</b> for a gradient echo sequence <b>182</b> utilized to measure eddy currents with long time constants (e.g., having eddy current excitation gradients with positive polarity). As described in greater detail below, the gradient echo sequence <b>182</b> is utilized as part of a train of the gradient echo sequences utilized to measure eddy currents with long time constants (e.g., wherein the estimated or measured eddy currents have a time constant at least two times longer than a time repetition of each gradient echo sequence of the train of gradient echo sequences). The gradient echo sequence <b>182</b> is configured to enable simultaneous generation and measurement of eddy currents (e.g., during a calibration scan such as an eddy current calibration scan).

The four rows <b>184</b>, <b>186</b>, <b>188</b>, and <b>190</b> illustrate the gradient echo sequence <b>182</b> utilized to measure eddy currents with long time constants. The first row <b>184</b> (e.g. top row) of the pulse sequence diagram <b>180</b> illustrates RF (represented along Y-axis <b>192</b>) over time (represented along X-axis <b>194</b>). As depicted, an RF pulse <b>196</b> is generated at approximately 1 millisecond. The second row <b>186</b> of the pulse sequence diagram <b>180</b> illustrates a gradient (represented along Y-axis <b>198</b> as gradient strength) applied along a frequency direction over time (represented along X-axis <b>200</b>). The gradient applied along the frequency direction is represented by plot <b>202</b>. A first portion <b>204</b> of the plot <b>202</b> located to the left of dashed line <b>206</b> is a balanced gradient echo having a zero gradient area. A second portion <b>208</b> of the plot <b>202</b> located to the right of the dashed line <b>206</b> has an eddy current excitation gradient or eddy current generating gradient <b>210</b> having a positive polarity.

The third row <b>188</b> of the pulse sequence diagram <b>180</b> illustrates a gradient (represented along Y-axis <b>212</b> as gradient strength) applied along a phase direction over time (represented along X-axis <b>214</b>). The gradient applied along the phase direction is represented by plot <b>216</b>. A first portion <b>218</b> of the plot <b>216</b> located to the left of dashed line <b>220</b> is a balanced gradient echo having a zero gradient area. A second portion <b>222</b> of the plot <b>216</b> located to the right of the dashed line <b>222</b> has an eddy current excitation gradient or eddy current generating gradient <b>224</b> having a positive polarity.

The fourth row <b>190</b> (e.g., bottom row) of the pulse sequence diagram <b>180</b> illustrates a gradient (represented along Y-axis <b>226</b> as gradient strength) applied along a slice direction over time (represented along X-axis <b>228</b>). The gradient applied along the slice direction is represented by plot <b>230</b>. A first portion <b>232</b> of the plot <b>230</b> located to the left of dashed line <b>234</b> is a balanced gradient echo having a zero gradient area. A second portion <b>236</b> of the plot <b>230</b> located to the right of the dashed line <b>234</b> has an eddy current excitation gradient or eddy current generating gradient <b>238</b> having a positive polarity.

The balanced gradient echo of the first portions <b>204</b>, <b>216</b>, <b>232</b> of the applied gradients are utilized for eddy current measurement. The first portions <b>204</b> and <b>232</b> of the frequency gradient (e.g., readout gradient) and the slice gradient, respectively, are balanced to avoid eddy current effects from the frequency gradient and the slice gradient. The eddy current excitation gradients <b>210</b>, <b>224</b>, and <b>238</b> of the second portions <b>208</b>, <b>222</b>, and <b>236</b> are utilized for eddy current generation. The eddy current excitation gradients may be played along a single gradient axis at a time. When the eddy current excitation gradient is on the same axis with the readout gradient, the measured eddy current is commonly called on-axis eddy current. When the eddy current excitation gradient is not on the same axis with the readout gradient, the measured eddy current is commonly called cross-term eddy current. It is also possible to play one excitation gradient and do measurements along three axes sequentially so that both on-axis and cross-term eddy currents are measured in a single scan. The eddy current excitation gradients <b>210</b>, <b>224</b>, and <b>238</b> having positive polarity are utilized in conjunction with a gradient echo sequence (described in FIG. <b>3</b>) that includes eddy current excitation gradients having a negative polarity to form bipolar eddy current excitation gradients. These bipolar eddy current excitation gradients enable eddy currents to be distinguished from B<sub>0 </sub>drift since eddy currents change direction in response to the bipolar eddy current excitation gradients and B<sub>0 </sub>drift does not. The gradient echo sequence <b>182</b> is utilized in conjunction with a gradient echo sequence (described in FIG. <b>3</b>) to form a train of GRE sequences that are intermittently repeated (e.g., every 100 milliseconds (ms)) (e.g., as part of a pseudo-continuous scan) to measure eddy currents. The train of GRE sequences are utilized in conjunction with a GRE sequence (described in FIG. <b>4</b>) lacking eddy current excitation gradients.

FIG. <b>3</b> illustrates a pulse sequence diagram <b>240</b> for a gradient echo sequence <b>242</b> utilized to measure eddy currents with long time constants (e.g., having eddy current excitation gradients with negative polarity). As described in greater detail below, the gradient echo sequence <b>242</b> is utilized as part of a train of the gradient echo sequences utilized to measure eddy currents with long time constants (e.g., wherein the estimated or measured eddy currents have a time constant at least two times longer than a time repetition of each gradient echo sequence of the train of gradient echo sequences). The gradient echo sequence <b>242</b> is configured to enable simultaneous generation and measurement of eddy currents (e.g., during a calibration scan such as an eddy current calibration scan).

The four rows <b>244</b>, <b>246</b>, <b>248</b>, and <b>250</b> illustrate the gradient echo sequence <b>242</b> utilized to measure eddy currents with long time constants. The first row <b>244</b> (e.g. top row) of the pulse sequence diagram <b>240</b> illustrates RF (represented along Y-axis <b>252</b>) over time (represented along X-axis <b>254</b>). As depicted, an RF pulse <b>256</b> is generated at approximately 1 millisecond. The second row <b>246</b> of the pulse sequence diagram <b>240</b> illustrates a gradient (represented along Y-axis <b>258</b> as gradient strength) applied along a frequency direction over time (represented along X-axis <b>260</b>). The gradient applied along the frequency direction is represented by plot <b>262</b>. A first portion <b>264</b> of the plot <b>262</b> located to the left of dashed line <b>266</b> is a balanced gradient echo having a zero gradient area. A second portion <b>268</b> of the plot <b>262</b> located to the right of the dashed line <b>266</b> has an eddy current excitation gradient or eddy current generating gradient <b>270</b> having a negative polarity.

The third row <b>248</b> of the pulse sequence diagram <b>240</b> illustrates a gradient (represented along Y-axis <b>272</b> as gradient strength) applied along a phase direction over time (represented along X-axis <b>274</b>). The gradient applied along the phase direction is represented by plot <b>276</b>. A first portion <b>278</b> of the plot <b>276</b> located to the left of dashed line <b>280</b> is a balanced gradient echo having a zero gradient area. A second portion <b>282</b> of the plot <b>276</b> located to the right of the dashed line <b>280</b> has an eddy current excitation gradient or eddy current generating gradient <b>284</b> having a negative polarity.

The fourth row <b>250</b> (e.g., bottom row) of the pulse sequence diagram <b>240</b> illustrates a gradient (represented along Y-axis <b>286</b> as gradient strength) applied along a slice direction over time (represented along X-axis <b>288</b>). The gradient applied along the slice direction is represented by plot <b>290</b>. A first portion <b>292</b> of the plot <b>290</b> located to the left of dashed line <b>294</b> is a balanced gradient echo having a zero gradient area. A second portion <b>296</b> of the plot <b>290</b> located to the right of the dashed line <b>294</b> has an eddy current excitation gradient or eddy current generating gradient <b>296</b> having a negative polarity.

The balanced gradient echo of the first portions <b>264</b>, <b>278</b>, <b>292</b> of the applied gradients are utilized for eddy current measurement. The first portions <b>264</b> and <b>292</b> of the frequency gradient (e.g., readout gradient) and the slice gradient, respectively, are balanced to avoid eddy current effects from the frequency gradient and the slice gradient. The eddy current excitation gradients <b>270</b>, <b>284</b>, and <b>298</b> of the second portions <b>268</b>, <b>282</b>, and <b>296</b> are utilized for eddy current generation. The eddy current excitation gradients <b>270</b>, <b>284</b>, and <b>298</b> having negative polarity are utilized in conjunction with a gradient echo sequence (described in FIG. <b>2</b>) that includes eddy current excitation gradients having a positive polarity to form bipolar eddy current excitation gradients. These bipolar eddy current excitation gradients enable eddy currents to be distinguished from B<sub>0 </sub>drift since eddy currents change direction in response to the bipolar eddy current excitation gradients and B<sub>0 </sub>drift does not. The gradient echo sequence <b>242</b> is utilized in conjunction with a gradient echo sequence (described in FIG. <b>2</b>) to form a train of GRE sequences that are intermittently repeated (e.g., every 100 milliseconds (ms)) (e.g., as part of a pseudo-continuous scan) to measure eddy currents. The train of GRE sequences are utilized in conjunction with a GRE sequence (described in FIG. <b>4</b>) lacking eddy current excitation gradients.

FIG. <b>4</b> illustrates a pulse sequence diagram <b>300</b> for a gradient echo sequence <b>302</b> utilized to measure eddy currents with long time constants (e.g., lacking eddy current excitation gradients). As described in greater detail below, the gradient echo sequence <b>302</b> is utilized in conjunction with a train of the gradient echo sequences (those described in FIGS. <b>2</b> and <b>3</b>) to measure eddy currents with long time constants (e.g., wherein the estimated or measured eddy currents have a time constant at least two times longer than a time repetition of each gradient echo sequence of the train of gradient echo sequences). The gradient echo sequence <b>302</b> is configured removing background fields for measurement of eddy currents (e.g., during a calibration scan such as an eddy current calibration scan).

The four rows <b>304</b>, <b>306</b>, <b>308</b>, and <b>310</b> illustrate the gradient echo sequence <b>302</b> utilized to measure eddy currents with long time constants. The first row <b>304</b> (e.g. top row) of the pulse sequence diagram <b>300</b> illustrates RF (represented along Y-axis <b>312</b>) over time (represented along X-axis <b>314</b>). As depicted, an RF pulse <b>316</b> is generated at approximately 1 millisecond. The second row <b>306</b> of the pulse sequence diagram <b>302</b> illustrates a gradient (represented along Y-axis <b>318</b> as gradient strength) applied along a frequency direction over time (represented along X-axis <b>320</b>). The gradient applied along the frequency direction is represented by plot <b>322</b>. A first portion <b>324</b> of the plot <b>322</b> located to the left of dashed line <b>326</b> is a balanced gradient echo having a zero gradient area. A second portion <b>328</b> of the plot <b>322</b> located to the right of the dashed line <b>326</b> lacks an eddy current excitation gradient or eddy current generating gradient.

The third row <b>308</b> of the pulse sequence diagram <b>300</b> illustrates a gradient (represented along Y-axis <b>330</b> as gradient strength) applied along a phase direction over time (represented along X-axis <b>332</b>). The gradient applied along the phase direction is represented by plot <b>334</b>. A first portion <b>336</b> of the plot <b>334</b> located to the left of dashed line <b>338</b> is a balanced gradient echo having a zero gradient area. A second portion <b>340</b> of the plot <b>334</b> located to the right of the dashed line <b>338</b> lacks an eddy current excitation gradient or eddy current generating gradient.

The fourth row <b>310</b> (e.g., bottom row) of the pulse sequence diagram <b>300</b> illustrates a gradient (represented along Y-axis <b>342</b> as gradient strength) applied along a slice direction over time (represented along X-axis <b>344</b>). The gradient applied along the slice direction is represented by plot <b>346</b>. A first portion <b>348</b> of the plot <b>346</b> located to the left of dashed line <b>350</b> is a balanced gradient echo having a zero gradient area. A second portion <b>352</b> of the plot <b>346</b> located to the right of the dashed line <b>350</b> lacks an eddy current excitation gradient or eddy current generating gradient.

The balanced gradient echo of the first portions <b>324</b>, <b>336</b>, <b>348</b> of the applied gradients are utilized for eddy current measurement. The first portions <b>324</b> and <b>348</b> of the frequency gradient (e.g., readout gradient) and the slice gradient, respectively, are balanced to avoid eddy current effects from the frequency gradient and the slice gradient. The lack of eddy current excitation gradients in the second portions <b>328</b>, <b>340</b>, and <b>352</b> enable the removal of background fields. The gradient echo sequence <b>302</b> is utilized in conjunction with a train of GRE sequences (as described in FIGS. <b>2</b> and <b>3</b>) that are intermittently repeated (e.g., every 100 milliseconds (ms)) (e.g., as part of a pseudo-continuous scan) to measure eddy currents.

FIG. <b>5</b> illustrates a flow chart of a method <b>354</b> for measuring eddy currents with long time constants. One or more steps of the method <b>354</b> may be performed by processing circuitry of the magnetic resonance imaging system <b>100</b> in FIG. <b>1</b>. One or more of the steps of the method <b>354</b> may be performed simultaneously or in a different order from the order depicted in FIG. <b>5</b>.

The method <b>354</b> includes initiating a calibration scan (e.g., eddy current calibration scan) of a phantom utilizing a magnetic resonance imaging scanner (e.g., MR scanner <b>102</b> in FIG. <b>1</b>) of a magnetic resonance imaging system (block <b>356</b>). The calibration scan may be performed during installation of MRI system and/or after maintenance on the MRI system.

The method <b>354</b> also includes utilizing a train of gradient echo (GRE) sequences to simultaneously generate and measure the eddy currents during the calibration scan (block <b>358</b>). The train of gradient echo sequences includes gradient echo sequences that each include a first portion having a balanced gradient echo sequence (with zero gradient area) for eddy current measurement. The balanced gradient echo of each of these gradient echo sequences of the train have a balanced readout gradient and slice gradient to avoid eddy current effect from the readout gradient and the slice gradient. For example, gradient echo sequences <b>182</b> and <b>242</b> of FIGS. <b>2</b> and <b>3</b>, respectively, each have balanced gradient echo sequences and may be utilized in the train of gradient echo sequences.

The train of gradient echo sequences also includes a first set of gradient echo sequences having a second portion having an eddy current excitation gradient or eddy current generating gradient having a positive polarity. For example, gradient echo sequence <b>182</b> of FIG. <b>2</b> has an eddy current excitation gradient or eddy current generating gradient having a positive polarity and may be utilized in the train of gradient echo sequences.

The train of gradient echo sequences also includes a second set of gradient echo sequences having a second portion having an eddy current excitation gradient or eddy current generating gradient having a negative polarity. For example, gradient echo sequence <b>242</b> of FIG. <b>3</b> has an eddy current excitation gradient or eddy current generating gradient having a negative polarity and may be utilized in the train of gradient echo sequences. The utilization of the first set of gradient echo sequences having a second portion having an eddy current excitation gradient or eddy current generating gradient having a positive polarity and the second set of gradient echo sequences having a second portion having an eddy current excitation gradient or eddy current generating gradient having a negative polarity form bipolar eddy current excitation gradients. These bipolar eddy current excitation gradients enable eddy currents to be distinguished from B<sub>0 </sub>drift since eddy currents change direction in response to the bipolar eddy current excitation gradients and B<sub>0 </sub>drift does not.

In conjunction with the train of GRE sequences, a GRE sequence having both a first portion having a balanced gradient echo sequence for eddy current measurement and a second portion lacking an eddy current excitation gradient or eddy current generating gradient may be utilized. For example, gradient echo sequence <b>302</b> in FIG. <b>4</b> may be utilized in conjunction with the train of GRE sequences. In particular, the gradient echo sequence <b>302</b> may be utilized prior to the train of gradient echo sequences to establish a baseline to remove background fields. In addition, the gradient echo sequence <b>302</b> may be utilized after the train of gradient echo sequences.

The gradient echo sequences utilized in train of gradient echo sequences (as well as the gradient echo sequence lacking an eddy current excitation gradient or eddy current generating gradient) are repeated at a regular rate as part of a pseudo-continuous scan (i.e., the eddy current calibration scan). In certain embodiments, the timing can be changed for repeating the gradient echo sequences as long as the pseudo-continuous condition is maintained and the average gradient area remains constant. In certain embodiments, these gradient echo sequences may be utilized in single pass to measure the eddy currents with long time constants. For example, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may first be repeated for a set number of times. Then, the gradient echo sequence having an eddy current excitation gradient with positive polarity (e.g., gradient echo sequence <b>182</b>) is repeated for a set number of times, followed by repeating the gradient echo sequence having an eddy current excitation gradient with negative polarity (e.g., gradient echo sequence <b>242</b>) a set number of times. Finally, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may then be repeated a set number of times. In certain embodiments, the respective set number of times that the gradient echo sequence having an eddy current excitation gradient with positive polarity and the gradient echo sequence having an eddy current excitation gradient with negative polarity are each repeated are the same. In certain embodiments, the respective set number of times that the gradient echo sequence having an eddy current excitation gradient with positive polarity and the gradient echo sequence having an eddy current excitation gradient with negative polarity are each repeated is greater than the set number of times that the gradient echo sequence lacking an eddy current excitation gradient is repeated. In certain embodiments, the set number of times the gradient echo sequence lacking the eddy current excitation gradient is repeated at the end of the pseudo-continuous scan is greater the set number of times the gradient echo sequence lacking the eddy current excitation gradient is repeated at the beginning of the pseudo-continuous scan. The set number of times for repeating each of the gradient echo sequences for a pseudo-continuous scan for simultaneously generating and measuring eddy currents with long time constants may vary.

In certain embodiments (also for a single pass), the order of the gradient echo sequences may vary. For example, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may first be repeated for a set number of times. Then, the gradient echo sequence having an eddy current excitation gradient with negative polarity (e.g., gradient echo sequence <b>242</b>) is repeated for a set number of times, followed by repeating the gradient echo sequence having an eddy current excitation gradient with positive polarity (e.g., gradient echo sequence <b>182</b>) a set number of times. Finally, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may then be repeated a set number of times. In certain embodiments, the respective set number of times that the gradient echo sequence having an eddy current excitation gradient with negative polarity and the gradient echo sequence having an eddy current excitation gradient with positive polarity are each repeated are the same. In certain embodiments, the respective set number of times that the gradient echo sequence having an eddy current excitation gradient with negative polarity and the gradient echo sequence having an eddy current excitation gradient with positive polarity are each repeated is greater than the set number of times that the gradient echo sequence lacking an eddy current excitation gradient is repeated. In certain embodiments, the set number of times the gradient echo sequence lacking the eddy current excitation gradient is repeated at the end of the pseudo-continuous scan is greater the set number of times the gradient echo sequence lacking the eddy current excitation gradient is repeated at the beginning of the pseudo-continuous scan. The set number of times for repeating each of the gradient echo sequences for a pseudo-continuous scan for simultaneously generating and measuring eddy currents with long time constants may vary.

In certain embodiments, multiple passes (e.g., two passes) may be utilized for measuring eddy currents with long time constants. In a first pass, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may first be repeated for a set number of times. Then, the gradient echo sequence having an eddy current excitation gradient with positive polarity (e.g., gradient echo sequence <b>182</b>) is repeated for a set number of times. Finally, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may then be repeated a set number of times. In a second pass, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may first be repeated for a set number of times. Then, the gradient echo sequence having an eddy current excitation gradient with negative polarity (e.g., gradient echo sequence <b>242</b>) is repeated for a set number of times. Finally, the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b>) may then be repeated a set number of times. In certain embodiments, the respective set number of times that the gradient echo sequence having an eddy current excitation gradient with positive polarity and the gradient echo sequence having an eddy current excitation gradient with negative polarity are each repeated are the same. In certain embodiments, the gradient echo sequence having an eddy current excitation gradient with negative polarity may be utilized in the first pass and the gradient echo sequence having an eddy current excitation gradient with positive polarity may be utilized in the second pass.

Notwithstanding the prior reference to using a set number of repetitions of the gradient echo sequence, in certain embodiments the number of times for repeating of each gradient echo sequences may be adaptively varied during a test session in response to the analysis of the prior acquired gradient echo sequences.

Returning to FIG. <b>5</b>, the method <b>354</b> further includes acquiring k-space data from the train of gradient echo sequences (as well as the gradient echo sequences lacking an eddy current excitation gradient) (block <b>360</b>). The method <b>354</b> even further includes converting the k-space data to eddy current gradient fields (block <b>362</b>). Converting the k-space data to eddy current gradient fields may include a number of steps. In certain embodiments, each line of k-space data may be subjected to one-dimensional Fourier transformation to generate complex data. Phase information may be obtained from the complex data and the phase information along with linear regression may be utilized to obtain a slope and intercept to determine the eddy current gradient fields. The slope provides the spatially linear term of the eddy current. The intercept provides the spatially independent B<sub>0 </sub>term.

The method <b>354</b> yet further includes estimating the eddy currents as a function of time based on the eddy current gradient fields (block <b>364</b>). The induced eddy current can be approximated as resulting from a constant gradient with a duration equal to the time repetition and an amplitude equivalent to an average gradient, wherein the average gradient is a total gradient area of a respective gradient echo sequence of the train of gradient echo sequences divided by the time repetition. In certain embodiments, estimating the eddy currents as a function of time includes scaling the eddy current gradient fields by an average gradient strength and fitting the scaled eddy current gradient fields as a function of time. In particular, estimating the eddy currents as a function of time (G<sub>ec</sub>(t)) involves utilizing the following equation:

G
        
         e
         ⁢
         c
        
       
       (
       t
       )
      
      =
      
       
        G
        
         a
         ⁢
         v
         ⁢
         e
        
       
       *
       α
       *
       
        (
        
         1
         -
         
          e
          
           
            -
            t
           
           /
           TC
          
         
        
        )
       
      
     
     ,
    
   
   
    
     (
     1
     )
    
   
  
 


<br/>
wherein G<sub>ave </sub>is an average gradient, α is an eddy current amplitude in percentage, t is time, and TC is a time constant of a respective eddy current. As noted above, the average gradient, G<sub>ave</sub>, is the total gradient area divided by the time repetition of the gradient echo sequence. The average gradient is determined by the gradient echo sequence. The eddy current amplitude in percentage, α, is unknown. The time constant is also unknown. The method <b>354</b> enables the measurement of the time constant and the amplitude accurately when the sequence time repetition is much shorter than the time constant (i.e., the time constant is at least two times the time repetition).

The method <b>354</b> even further includes storing the estimated eddy currents (block <b>366</b>). The estimated eddy currents may be utilized for correcting acquired MR scan data.

As noted above, the method <b>354</b> in FIG. <b>5</b> enables the measurement of the time constant and the amplitude of Equation 1 accurately when the sequence time repetition is much shorter than the time constant (i.e., the time constant is at least two times the time repetition). This is demonstrated in FIGS. <b>6</b>-<b>9</b> which are graphs illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein at various eddy current time constants as part of a test procedure. It should be noted that FIGS. <b>6</b>-<b>9</b> is part of a test to prove that the method <b>354</b> in FIG. <b>5</b> works. Injected eddy current tests are not part of the normal operation of the method <b>354</b>.

The test procedure includes dialing in the linear eddy current along the frequency direction at amplitude (a) of −1.0% and varying time constants (e.g., 0.01 seconds, 0.1 seconds, 1 second, and 10 seconds). The eddy currents are measured utilizing the method <b>354</b> described in FIG. <b>5</b>. The gradient echo sequence utilized (e.g., as described in FIGS. <b>2</b>-<b>4</b>) has a time repetition of 100 ms. The eddy current excitation gradient (for the positive polarity and the negative polarity) is applied along the frequency direction only. The average gradient strength is 1.5 G/cm. The full scan includes a sequence of 10 repetitions of a gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b> in FIG. <b>4</b>), followed in order by 200 repetitions of a gradient echo sequence having an eddy current excitation gradient with positive polarity (e.g., gradient echo sequence <b>182</b> in FIG. <b>2</b>), 200 repetitions of a gradient echo sequence having an eddy current excitation gradient with negative polarity (e.g., gradient echo sequence <b>242</b> in FIG. <b>3</b>), another 200 repetitions of the gradient echo sequence having an eddy current excitation gradient with positive polarity (e.g., gradient echo sequence <b>182</b> in FIG. <b>2</b>), another 200 repetitions of the gradient echo sequence having an eddy current excitation gradient with negative polarity (e.g., gradient echo sequence <b>242</b> in FIG. <b>3</b>), and finally 214 repetitions of the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b> in FIG. <b>4</b>).

In the test procedure, the first 10 repetitions of the gradient echo sequence lacking an eddy current excitation gradient (e.g., gradient echo sequence <b>302</b> in FIG. <b>4</b>) are treated as baseline. Also, the first repetition with the gradient echo sequence having an eddy current excitation gradient with positive polarity (e.g., gradient echo sequence <b>182</b> in FIG. <b>2</b>) is set at time equaling 0 seconds. The measured raw data is then converted to eddy current gradient fields as described utilizing the method <b>354</b> in FIG. <b>5</b>. The calculated eddy current gradient is then scaled by the average gradient strength and fit as a function of time utilizing Equation 1 described above. This is done for each of the different eddy current time constants.

FIG. <b>6</b> is a graph <b>368</b> illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 0.01 seconds) as part of the test procedure. FIG. <b>7</b> is a graph <b>370</b> illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 0.1 seconds) as part of the test procedure. FIG. <b>8</b> is a graph <b>372</b> illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 1 second) as part of the test procedure. FIG. <b>9</b> is a graph <b>374</b> illustrating measured eddy current values fitted as a function of time utilizing the techniques described herein (e.g., with an eddy current time constant of 10 seconds) as part of the test procedure. Each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b> has a Y-axis <b>376</b> representing the eddy current gradient (in percentage) and an X-axis <b>378</b> representing time (in seconds (sec)). Point <b>380</b> in each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b> represents the first data point at time=0 (the impact of baseline has been removed by subtracting the average of eddy current gradient fields from the 10 repetitions of the gradient echo sequence lacking the eddy current excitation gradient). Section <b>382</b> in each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b> represents the data from the first 200 repetitions of the gradient echo sequence having the eddy current excitation gradient with a positive polarity. Section <b>384</b> in each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b> represents the data from the first 200 repetitions of the gradient echo sequence having the eddy current excitation gradient with a negative polarity. Section <b>386</b> in each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b> represents the data from the second 200 repetitions of the gradient echo sequence having the eddy current excitation gradient with a positive polarity. Section <b>388</b> in each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b> represents the data from the second 200 repetitions of the gradient echo sequence having the eddy current excitation gradient with a negative polarity. Section <b>390</b> in each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b> represents the data from the last 214 repetitions of the gradient echo sequence lacking the eddy current excitation gradient. In each of the graphs <b>368</b>, <b>370</b>, <b>372</b>, <b>374</b>, the open circles represent the measured data and the line the fitting of the measured data.

With respect to the data in the graph <b>368</b>, the ground truth for the time constant was 0.01 seconds and the ground truth for amplitude (α) was −1.0% while the fitted result for the measured time constant was 0.017 seconds and the fitted result for amplitude (α) was −0.20%. With respect to the data in the graph <b>370</b>, the ground truth for the time constant was 0.1 seconds and the ground truth for amplitude (α) was −1.0% while the fitted result for the measured time constant was 0.10 seconds and the fitted result for amplitude (α) was −0.93%. With respect to the data in the graph <b>372</b>, the ground truth for the time constant was 1 second and the ground truth for amplitude (α) was −1.0% while the fitted result for the measured time constant was 1.01 seconds and the fitted result for amplitude (α) was −1.00%. With respect to the data in the graph <b>374</b>, the ground truth for the time constant was 10 seconds and the ground truth for amplitude (α) was −1.0% while the fitted result for the measured time constant was 10.12 seconds and the fitted result for amplitude (α) was −1.01%. The data in the graphs <b>372</b>, <b>374</b> illustrates that the described method <b>354</b> in FIG. <b>5</b> can measure the time constant and the amplitude accurately when the time repetition of the gradient echo sequence is much shorter than the time constant (i.e., the time constant is at least 2 times the time repetition of the gradient echo sequence). The data in the graphs <b>368</b>, <b>370</b> illustrates that when the time repetition of gradient echo sequence is comparable with or shorter than the time constant, the eddy current cannot be quantified accurately by the method <b>354</b> described in FIG. <b>5</b> because the average gradient assumption requires that the time repetition of the gradient echo sequence be much shorter than the time constant. Thus, the method <b>354</b> described in FIG. <b>5</b> can be utilized to measure eddy currents with long time constants.

In certain embodiments, instead of a gradient echo sequence, a free induction decay sequence may be utilized for data collection in measuring eddy currents with long time constants. FIG. <b>10</b> illustrates a pulse sequence diagram <b>392</b> for a free induction decay sequence <b>394</b> utilized to measure eddy currents with long time constants (e.g., having eddy current excitation gradients with positive polarity). It should be noted that small localized samples (e.g., six samples with two samples each aligned along X, Y, and Z axes to localize the field measurements) having transmit and receiving coils (e.g., as part of a GRAFIDY tool kit) are utilized instead of a large phantom when free induction decay sequences are utilized in measuring eddy currents with long time constants.

The four rows <b>396</b>, <b>398</b>, <b>400</b>, and <b>402</b> illustrate the free induction decay sequence <b>394</b> utilized to measure eddy currents with long time constants. The first row <b>396</b> (e.g. top row) of the pulse sequence diagram <b>392</b> illustrates RF (represented along Y-axis <b>404</b>) over time (represented along X-axis <b>406</b>). As depicted, an RF pulse <b>408</b> is generated at approximately 1 millisecond. The second row <b>398</b> of the pulse sequence diagram <b>392</b> illustrates a gradient (represented along Y-axis <b>410</b> as gradient strength) applied along a frequency direction over time (represented along X-axis <b>412</b>). The gradient applied along the frequency direction is represented by plot <b>414</b>. A first portion <b>416</b> of the plot <b>414</b> located to the left of dashed line <b>418</b> is a free induction decay having a zero gradient area. A second portion <b>420</b> of the plot <b>414</b> located to the right of the dashed line <b>418</b> has an eddy current excitation gradient or eddy current generating gradient <b>422</b> having a positive polarity.

The third row <b>400</b> of the pulse sequence diagram <b>392</b> illustrates a gradient (represented along Y-axis <b>424</b> as gradient strength) applied along a phase direction over time (represented along X-axis <b>426</b>). The gradient applied along the phase direction is represented by plot <b>428</b>. A first portion <b>430</b> of the plot <b>428</b> located to the left of dashed line <b>432</b> is a free induction decay having a zero gradient area. A second portion <b>434</b> of the plot <b>428</b> located to the right of the dashed line <b>432</b> has an eddy current excitation gradient or eddy current generating gradient <b>436</b> having a positive polarity.

The fourth row <b>402</b> (e.g., bottom row) of the pulse sequence diagram <b>392</b> illustrates a gradient (represented along Y-axis <b>438</b> as gradient strength) applied along a slice direction over time (represented along X-axis <b>440</b>). The gradient applied along the slice direction is represented by plot <b>442</b>. A first portion <b>444</b> of the plot <b>442</b> located to the left of dashed line <b>446</b> is a free induction decay having a zero gradient area. A second portion <b>450</b> of the plot <b>442</b> located to the right of the dashed line <b>446</b> has an eddy current excitation gradient or eddy current generating gradient <b>448</b> having a positive polarity.

The free induction decay of the first portions <b>416</b>, <b>430</b>, <b>444</b> of the applied gradients are utilized for eddy current measurement. The first portions <b>204</b> and <b>232</b> of the frequency gradient (e.g., readout gradient) and the slice gradient, respectively, are balanced to avoid eddy current effects from the frequency gradient and the slice gradient. The eddy current excitation gradients <b>422</b>, <b>436</b>, and <b>448</b> of the second portions <b>420</b>, <b>434</b>, and <b>450</b> are utilized for eddy current generation. The eddy current excitation gradients <b>422</b>, <b>436</b>, and <b>450</b> having positive polarity are utilized in conjunction with a free induction decay sequence that includes eddy current excitation gradients having a negative polarity to form bipolar eddy current excitation gradients. These bipolar eddy current excitation gradients enable eddy currents to be distinguished from B<sub>0 </sub>drift since eddy currents change direction in response to the bipolar eddy current excitation gradients and B<sub>0 </sub>drift does not. The free induction decay sequence <b>394</b> is utilized in conjunction with a free induction decay sequence (to form a train of free induction decay sequences that are intermittently repeated (e.g., every 100 milliseconds (ms)) (e.g., as part of a pseudo-continuous scan) to measure eddy currents. The train of free induction decay sequences are utilized in conjunction with a free induction decay sequence lacking eddy current excitation gradients.

Technical effects of the disclosed subject matter include enabling measurement of eddy currents with long time constants utilizing a gradient echo sequence. Technical effects of the disclosed subject matter also include enabling the simultaneous generation and measurement eddy currents. This enables a pseudo-continuous scan (with the train of GRE sequences intermittently repeated) to be utilized to measure eddy currents with long time constants that takes less time and is more efficient than previous techniques. In addition, the disclosed subject matter is less sensitive to B<sub>0 </sub>drift. Technical effects of the disclosed subject matter further include improving the accuracy of calibration for eddy currents with very long time constants. By increasing the accuracy of the calibration, image quality is improved in certain MR images.

The techniques presented and claimed herein are referenced and applied to material objects and concrete examples of a practical nature that demonstrably improve the present technical field and, as such, are not abstract, intangible or purely theoretical. Further, if any claims appended to the end of this specification contain one or more elements designated as “means for [perform]ing [a function] . . . ” or “step for [perform]ing [a function] . . . ”, it is intended that such elements are to be interpreted under 35 U.S.C. 112(f). However, for any claims containing elements designated in any other manner, it is intended that such elements are not to be interpreted under 35 U.S.C. 112(f).

This written description uses examples to disclose the present subject matter, including the best mode, and also to enable any person skilled in the art to practice the subject matter, including making and using any devices or systems and performing any incorporated methods. The patentable scope of the subject matter is defined by the claims, and may include other examples that occur to those skilled in the art. Such other examples are intended to be within the scope of the claims if they have structural elements that do not differ from the literal language of the claims, or if they include equivalent structural elements with insubstantial differences from the literal languages of the claims.

## Claims

1. A computer-implemented method for measuring eddy currents with long time constants, comprising:
initiating, via a processor, a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner;
utilizing, via the processor, a train of gradient echo sequences to simultaneously generate and measure the eddy currents during the calibration scan, wherein both eddy current generation and measurement are completed within each gradient echo sequence of the train of gradient echo sequences;
acquiring, via the processor, k-space data from the train of gradient echo sequences;
converting, via the processor, the k-space data to eddy current gradient fields; and
estimating, via the processor, the eddy currents as a function of time based on the eddy current gradient fields.

2. The computer-implemented method of claim 1, wherein a first portion of each gradient echo sequence of the train of gradient echo sequences comprises a balanced gradient echo for eddy current measurement, wherein the balanced gradient echo has a balanced readout gradient and slice gradient to avoid eddy current effect.

3. The computer-implemented method of claim 2, wherein a second portion of a set of gradient echo sequences of the train of gradient echo sequences comprises an eddy current excitation gradient for eddy current generation.

4. The computer-implemented method of claim 3, wherein the second portion of some gradient echo sequences of the set of gradient echo sequences comprises a negative eddy current excitation gradient and the second portion of some gradient echo sequences of the set of gradient echo sequences comprises a positive eddy current excitation gradient.

5. The computer-implemented method of claim 1, wherein the estimated eddy currents have a time constant at least two times longer than a time repetition of each gradient echo sequence of the train of gradient echo sequences.

6. The computer-implemented method of claim 5, wherein the induced eddy current can be approximated as resulting from a constant gradient with a duration equal to the time repetition and an amplitude equivalent to an average gradient, wherein the average gradient is a total gradient area of a respective gradient echo sequence of the train of gradient echo sequences divided by the time repetition.

7. The computer-implemented method of claim 5, wherein estimating the eddy currents as a function of time comprises scaling the eddy current gradient fields by an average gradient strength and fitting the scaled eddy current gradient fields as a function of time.

8. The computer-implemented method of claim 5, wherein estimating the eddy currents as a function of time (G<sub>ec</sub>(t)) comprises utilizing the following equation:



 
  
   
    
     G
     ec
    
    (
    t
    )
   
   =
   
    
     G
     ave
    
    *
    α
    *
    
     (
     
      1
      -
      
       e
       
        
         -
         t
        
        /
        TC
       
      
     
     )
    
   
  
  ,
 



wherein G<sub>ave </sub>is an average gradient, α is an eddy current amplitude in percentage, t is time, and TC is a time constant of a respective eddy current.

9. A system for measuring eddy currents with long time constants, comprising:
a memory encoding processor-executable routines; and
a processor configured to access the memory and to execute the processor-executable routines, wherein the processor-executable routines, when executed by the processor, cause the processor to:
initiate a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner;
utilize a train of gradient echo sequences to simultaneously generate and measure the eddy currents during the calibration scan, wherein both eddy current generation and measurement are completed within each gradient echo sequence of the train of gradient echo sequences;
acquire k-space data from the train of gradient echo sequences;
convert the k-space data to eddy current gradient fields; and
estimate the eddy currents as a function of time based on the eddy current gradient fields.

10. The system of claim 9, wherein a first portion of each gradient echo sequence of the train of gradient echo sequences comprises a balanced gradient echo for eddy current measurement, wherein the balanced gradient echo has a balanced readout gradient and slice gradient to avoid eddy current effect.

11. The system of claim 10, wherein a second portion of a set of gradient echo sequences of the train of gradient echo sequences comprises an eddy current excitation gradient for eddy current generation.

12. The system of claim 11, wherein the second portion of some gradient echo sequences of the set of gradient echo sequences comprises a negative eddy current excitation gradient and the second portion of some gradient echo sequences of the set of gradient echo sequences comprises a positive eddy current excitation gradient.

13. The system of claim 9, wherein the estimated eddy currents have a time constant at least two times longer than a time repetition of each gradient echo sequence of the train of gradient echo sequences.

14. The system of claim 13, wherein the induced eddy current can be approximated as resulting from a constant gradient with a duration equal to the time repetition and an amplitude equivalent to an average gradient, wherein the average gradient is a total gradient area of a respective gradient echo sequence of the train of gradient echo sequences divided by the time repetition.

15. The system of claim 13, wherein estimating the eddy currents as a function of time comprises scaling the eddy current gradient fields by an average gradient strength and fitting the scaled eddy current gradient fields as a function of time.

16. The system of claim 13, wherein estimating the eddy currents as a function of time (G<sub>ec</sub>(t)) comprises utilizing the following equation:



 
  
   
    
     G
     ec
    
    (
    t
    )
   
   =
   
    
     G
     ave
    
    *
    α
    *
    
     (
     
      1
      -
      
       e
       
        
         -
         t
        
        /
        TC
       
      
     
     )
    
   
  
  ,
 



wherein G<sub>ave </sub>is an average gradient, α is an eddy current amplitude in percentage, t is time, and TC is a time constant of a respective eddy current.

17. A non-transitory computer-readable medium, the non-transitory computer-readable medium comprising processor-executable code that when executed by a processor, causes the processor to:
initiate a calibration scan of a phantom utilizing a magnetic resonance imaging (MRI) scanner;
utilize a train of gradient echo sequences to simultaneously generate and measure eddy currents during the calibration scan, wherein both eddy current generation and measurement are completed within each gradient echo sequence of the train of gradient echo sequences;
acquire k-space data from the train of gradient echo sequences;
convert the k-space data to eddy current gradient fields; and
estimate the eddy currents as a function of time based on the eddy current gradient fields.

18. The non-transitory computer-readable medium of claim 17, wherein the estimated eddy currents have a time constant at least two times longer than a time repetition of each gradient echo sequence of the train of gradient echo sequences.

19. The non-transitory computer-readable medium of claim 18, wherein estimating the eddy currents as a function of time comprises scaling the eddy current gradient fields by an average gradient strength and fitting the scaled eddy current gradient fields as a function of time.

20. The non-transitory computer-readable medium of claim 18, wherein estimating the eddy currents as a function of time (G<sub>ec</sub>(t)) comprises utilizing the following equation:



 
  
   
    
     G
     ec
    
    (
    t
    )
   
   =
   
    
     G
     ave
    
    *
    α
    *
    
     (
     
      1
      -
      
       e
       
        
         -
         t
        
        /
        TC
       
      
     
     )
    
   
  
  ,
 



wherein G<sub>ave </sub>is an average gradient, α is an eddy current amplitude in percentage, t is time, and TC is a time constant of a respective eddy current.

