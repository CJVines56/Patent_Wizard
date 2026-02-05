# Systems and methods for monitoring hydraulic systems (Doc 12405249)

- Doc ID: 12405249
- Title: Systems and methods for monitoring hydraulic systems
- Filing Date: 20240304
- Classification: G01N 29/024
- Authors: Daniel Gysling

## Abstract

A fluid monitoring system is disclosed that may include a piping network having, a flexible hydraulic hose having a hose length, a hose diameter a first end portion and a second end portion. In addition, the fluid monitoring system may include a first fitting coupled to the first end portion and a second fitting coupled to the second end portion. The fluid monitoring system may include an acoustic array having a first acoustic pressure sensor positioned proximate the first fitting, a second acoustic pressure sensor positioned proximate the second fitting, and an acoustic aperture that spans an aperture length between the first acoustic pressure sensor and the second acoustic pressure sensor. The fluid monitoring system may include a processing unit that determines a speed of sound of a process fluid within the piping network and within acoustic aperture using the first acoustic pressure sensor and the second acoustic pressure sensor.

## Description

This application claims priority to Patent Cooperation Treaty Application Number PCT/US2024/018340 having an International filing date of 4 Mar. 2024, as well as U.S. Provisional Patent Application No. 63/488,100, filed on 3 Mar. 2023, the disclosure of the prior Applications are considered part of and are incorporated by reference into this patent application in their entirety.

It is known in the prior art that entrained air can cause significantly impair operability, reduce longevity, and reduce the efficiency of hydraulic systems. Entrained air can cause excess heating of the hydraulic fluid, as well as “dieseling” in which, upon compression of bubbly hydraulic fluids, the mixture ignites, causing oxidation and localized extreme temperatures, damaging seals and other surfaces.

FIG. <b>1</b> shows a schematic of a representative hydraulic system <b>1</b> of the prior art. Hydraulic system <b>1</b> includes various components including, for example, a reservoir <b>2</b>, a pump <b>3</b>, a control valve <b>4</b>, an inline filter <b>5</b>, a pressure relief valve <b>6</b> and an actuator or hydraulic cylinder <b>7</b>. The various components of hydraulic system <b>1</b> comprise a piping network filled with a hydraulic fluid (such as oil) hydraulically coupled by various conduits and hoses. It is quite common for such hydraulic systems to incorporate high pressure, yet flexible along their length, hydraulic hoses as part of the piping network. These hoses are often rubber or other type of flexible material, reinforced with steel, or other high strength/high modulus material. While the length flexibility of these hydraulic hoses provides important mechanical flexibility, the construction of the hose makes installing acoustics pressure sensors with the hydraulic hoses difficult. Reservoir <b>2</b> serves several purposes including providing sufficient working fluid to allow the actuator <b>7</b> the actuate over its full range, providing for thermal expansion of the fluid, serving as a heat exchanger to cool the working fluid, and, ideally, minimizing any entrained air with the hydraulic system <b>1</b>.

Entrained air can enter hydraulic systems through a variety of mechanisms, include air entrapped at oil/air interface within the reservoir, leaky seals and gaskets on the suction side of the pump, cavitation within the pump as well as out-gassing of dissolved air associated with temperature changes of the hydraulic oil. Air entrapment, and subsequent gas carry-under through the liquid outlet of a reservoir, can be an important source of entrained air with a hydraulic system. The amount of entrained air entering a hydraulic system can vary with the design of the system as well and with operating conditions, such as oil level within the reservoir and residence time of the oil within the reservoir, characteristics of the oil composition, temperature of the oil, and the amount and type of defoamers used, etc.

Entrained air can enter a hydraulic system, cause operability issues and damage components, and then exit, rendering issues with entrained air difficult to diagnose and mitigate.

Still referring to FIG. <b>1</b>, hydraulic system <b>1</b> can be of the type associated with a mobile system, such as earth mover. In hydraulic system <b>1</b>, the prime mover can be hydraulic pump <b>3</b> that is driven by a Power Take Off (PTO) shaft (not shown). The oil reservoir <b>2</b> can include an integrated cooling system. The components of the system can be connected by hydraulic hoses. In this particular example, actuator <b>7</b> can comprise a hydraulic motor.

Space and weight are important design parameters for many hydraulic systems, particularly mobile hydraulic systems. Mobile hydraulic systems tend to have smaller reservoirs, larger range of operating temperature, larger range of power supplied, and are subject to motion (creating sloshing in reservoir). All of these issues can cause increased variability in entrained air levels within the hydraulic system compared to stationary hydraulic systems. In addition to entrained air, contamination and oil degradation can occur and have deleterious effects on hydraulic system <b>1</b>.

Mobile hydraulic systems typically utilize flexible hydraulic hoses to connect the various components, in part due to the physical constraints of installing the systems on a mobile vehicle. The flexible hoses of such mobile systems are capable of withstanding high pressures and typically have metal fittings on each end to secure the hose to the various component within the system.

The hydraulic hoses in the hydraulic system are typically terminated with some type of connector that forms a conduit that, compared to the hydraulic hose, is comparably rigid, and that facilitates connecting the hydraulic hoses to other components within the hydraulic system. These comparably rigid conduits terminating the hydraulic hoses can connect to the other components in a variety of methods. Some common connections include crimp and swage fittings and field-attachable fitting (also called quick-disconnect fittings). Typical connectors of the prior art can be found at https://www.discounthydraulichose.com/hose-fittings.html?gclid=EAlalQobChMIzsOo8_GB_QIVx8iGCh3zeQgaEAAYASAAEgLM_D_BwE.

What is needed is the ability to monitor the condition of the hydraulic fluid and to quantify the amount of entrained gas within hydraulic fluid systems on an intermittent or going basis. Quantifying the amount of entrained gas within a hydraulic system, whether the source is due to cavitation or air entrainment, leaks or other causes, would provide a significant advantage in the operation, optimization, and troubleshooting of hydraulic systems.

A system of one or more computers or processing units can be configured to perform particular operations or actions by virtue of having software, firmware, hardware, or a combination of them installed on the system that in operation causes or cause the system to perform the actions. One or more computer programs can be configured to perform particular operations or actions by virtue of including instructions that, when executed by data processing apparatus, cause the apparatus to perform the actions.

In one general aspect, a fluid measuring system may include a piping network having, a flexible hydraulic hose having a hose length, a hose diameter a first end portion and a second end portion. The fluid measuring system may also include a first fitting coupled to the first end portion and a second fitting coupled to the second end portion. The fluid measuring system may furthermore include an acoustic array having a first acoustic pressure sensor positioned proximate the first fitting, a second acoustic pressure sensor positioned proximate the second fitting, and an acoustic aperture that spans an aperture length between the first acoustic pressure sensor and the second acoustic pressure sensor. The fluid measuring system may in addition include a processing unit that determines a speed of sound of a process fluid within the piping network and within acoustic aperture using the first acoustic pressure sensor and the second acoustic pressure sensor. Other embodiments of this aspect include corresponding computer systems, apparatus, and computer programs recorded on one or more computer storage devices, each configured to perform the actions of the methods.

Implementations may include one or more of the following features. The fluid measuring system where the first acoustic pressure sensor and the second acoustic pressure sensor are not positioned on the flexible hydraulic hose. The fluid measuring system where the first fitting and the second fitting produce at least one change in a characteristic volumetric impedance within the acoustic aperture where the at least one change in a characteristic volumetric impedance is at least 25%. The fluid measuring system where the first fitting and the second fitting produce at least one change in a characteristic volumetric impedance within the acoustic aperture. The fluid measuring system may include a plurality of reflections of incident acoustic waves produced by the at least one change in a characteristic volumetric impedance in the process fluid within the aperture, and the processing unit is configured to determine the speed of sound of the process fluid within the acoustic aperture in the presence of the plurality of reflections of incident acoustic waves. The fluid measuring system where at least one of the first fitting and the second fitting may include at least a portion of a quick disconnect fitting. The fluid measuring system where the first fitting may include at least a portion of a first quick disconnect fitting and the second fitting may include at least a portion of a second quick disconnect fitting. The fluid measuring system where the first acoustic pressure sensor is positioned in the first quick disconnect fitting and the second acoustic pressure sensor is positioned in the second quick disconnect fitting. The fluid measuring system may include at least one manifold block coupled to any of the first fitting and the second fitting and where any of the first acoustic pressure sensor and the second acoustic pressure sensor is positioned in the at least one manifold block. The fluid measuring system where the first acoustic pressure sensor and the second acoustic pressure sensor are configured to be in fluid communication with the process fluid. The fluid measuring system where the first acoustic pressure sensor and the second acoustic pressure sensor may include piezo electric crystal pressure transducers. The fluid measuring system where the piping network further may include any of a reservoir, a pump, an actuator, a manifold, and a filter and where at least one of the first fitting and the second fitting is coupled to any of the reservoir, the pump, the actuator, the manifold, and the filter. The fluid measuring system may include the processing unit configured to determine an entrained air content of the process fluid using the speed of sound. The fluid measuring system may include the processing unit configured to determine a physical property of the process fluid using the speed of sound. The fluid measuring system may include the processing unit configured to determine changes in the process fluid using the speed of sound. The fluid measuring system may include the processing unit configured to determine a presence of at least one contaminate in the process fluid using the speed of sound. The fluid measuring system may include the processing unit configured to determine a diagnostic state of the piping network using the speed of sound. The fluid measuring system where the hose length is substantially equal to the acoustic aperture. The fluid measuring system where the flexible hydraulic hose is may include of an elastomer material. The fluid measuring system where the flexible hydraulic hose is may include of a composite having a plurality of materials and where the plurality of materials include at least one elastomer material and at least one reinforcing material. The fluid measuring system where the flexible hydraulic hose may include of an elastomer material having an elastic modulus of less than 1,000,000 psi and an elongation at yield of greater than 5%. The fluid measuring system where the aperture length is greater than ten times the hose diameter. The fluid measuring system where the piping network includes coherent acoustic waves, coherent vortical structures, and coherent propagating structural disturbances, and where the piping network is configured to preferentially reduce the coherence between the signals measured by the first acoustic pressure sensor and the second acoustic pressure sensor associated with the coherent vortical structures, and coherent propagating structural disturbances.

In one general aspect, the method of measuring a fluid may include providing a piping network having, a flexible hydraulic hose having a hose length, a hose diameter a first end portion and a second end portion. The method of measuring a fluid may also include a first fitting coupled to the first end portion and a second fitting coupled to the second end portion. The method of measuring a fluid may furthermore include an acoustic array having a first acoustic pressure sensor positioned proximate the first fitting, a second acoustic pressure sensor positioned proximate the second fitting, and an acoustic aperture that spans an aperture length between the first acoustic pressure sensor and the second acoustic pressure sensor. The method of measuring a fluid may in addition include providing a processing unit. The method of measuring a fluid may moreover include determining, with the processing unit, a speed of sound of a process fluid within the piping network and within acoustic aperture using the first acoustic pressure sensor and the second acoustic pressure sensor.

Implementations may include one or more of the following features. The method of measuring a fluid may include positioning the first acoustic pressure sensor and the second acoustic pressure sensor beyond the first end portion and the second end portion of the flexible hydraulic hose. The method of measuring a fluid may include producing at least one change in a characteristic volumetric impedance within the acoustic aperture where the at least one change in a characteristic volumetric impedance is at least 25%. The method of measuring a fluid may include producing at least one change in a characteristic volumetric impedance within the acoustic aperture. The method of measuring a fluid may include producing a plurality of reflections of incident acoustic waves using the at least one change in a characteristic volumetric impedance in the process fluid within the aperture, and determining with the processing unit the speed of sound of the process fluid within the acoustic aperture in the presence of the plurality of reflections of incident acoustic waves. The method of measuring a fluid where at least one of the first fitting and the second fitting may include at least a portion of a quick disconnect fitting. The method of measuring a fluid where the first fitting may include at least a portion of a first quick disconnect fitting and the second fitting may include at least a portion of a second quick disconnect fitting. The method of measuring a fluid may include positioning the first acoustic pressure sensor in the first quick disconnect fitting and positioning the second acoustic pressure sensor in the second quick disconnect fitting. The method of measuring a fluid may include coupling at least one manifold block to any of the first fitting and the second fitting and positioning any of the first acoustic pressure sensor and the second acoustic pressure sensor in the at least one manifold block. The method of measuring a fluid may include positioning the first acoustic pressure sensor and the second acoustic pressure sensor in fluid communication with the process fluid. The method of measuring a fluid where the first acoustic pressure sensor and the second acoustic pressure sensor may include piezo electric crystal pressure transducers. The method of measuring a fluid where the piping network further may include any of a reservoir, a pump, an actuator, a manifold, and a filter, the method may include coupling at least one of the first fitting and the second fitting to any of the reservoir, the pump, the actuator, the manifold, and the filter. The method of measuring a fluid may include determining, with the processing, an entrained air content of the process fluid using the speed of sound. The method of measuring a fluid may include determining, with the processing unit, a physical property of the process fluid using the speed of sound. The method of measuring a fluid may include the processing unit configured to determine changes in the process fluid using the speed of sound. The method of measuring a fluid may include determining, with the processing unit, a presence of at least one contaminate in the process fluid using the speed of sound. The method of measuring a fluid may include determining, with the processing unit, a diagnostic state of the piping network using the speed of sound. The method of measuring a fluid where the hose length is substantially equal to the acoustic aperture. The method of measuring a fluid where the flexible hydraulic hose is may include of an elastomer material. The method of measuring a fluid where the flexible hydraulic hose is may include of a composite having a plurality of materials and where the plurality of materials include at least one elastomer material and at least one reinforcing material. The method of measuring a fluid where the flexible hydraulic hose is may include of an elastomer material having an elastic modulus of less than 1,000,000 psi and an elongation at yield of greater than 5%. The method of measuring a fluid where the aperture length is greater than ten times the hose diameter. The method of measuring a fluid where the piping network includes coherent acoustic waves, coherent vortical structures, and coherent propagating structural disturbances, and the method further may include reducing the coherence between the signals measured by the first acoustic pressure sensor and the second acoustic pressure sensor associated with the coherent vortical structures, and coherent propagating structural disturbances. Implementations of the described techniques may include hardware, a method or process, or a computer tangible medium.

FIG. <b>1</b> is a schematic diagram of a hydraulic system of the prior art;

FIG. <b>2</b> is a schematic diagram of a connector for use in a hydraulic system of the prior art;

FIG. <b>3</b> is a schematic representation of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>4</b>A is a graphical representation of the relative amplitude between a pair of acoustic sensors in accordance with the present disclosure;

FIG. <b>4</b>B is a graphical representation of the phase angle between a pair of acoustic sensors in accordance with the present disclosure;

FIG. <b>5</b> is a graphical representation of the relative amplitude between a pair of acoustic sensors in accordance with the present disclosure;

FIG. <b>6</b> is a graphical representation of the phase angle between a pair of acoustic sensors in accordance with the present disclosure;

FIG. <b>7</b> is a graphical representation of the normalized beamforming power for various area ratios in accordance with the present disclosure;

FIG. <b>8</b> is a schematic representation of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>9</b> is a schematic representation of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>10</b> is a side cross sectional view of a sensor manifold of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>11</b> is a schematic representation of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>12</b> a graphical representation of the normalized beam forming power versus the speed of sound for water with a gas volume fraction in accordance with the present disclosure;

FIG. <b>13</b> a graphical representation of the normalized beam forming power versus the speed of sound for water with a gas volume fraction in accordance with the present disclosure;

FIG. <b>14</b> is a graphical representation of the measured sound speed versus the reference gas volume fraction in accordance with the present disclosure;

FIG. <b>15</b> is a graphical representation of the gas void fraction versus a reference gas void fraction in accordance with the present disclosure;

FIG. <b>16</b> is a schematic representation of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>17</b> is a schematic representation of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>18</b> is a schematic representation of the detail of inset <b>18</b> of FIG. <b>17</b> of a portion of a hydraulic monitoring system in accordance with the present disclosure;

FIG. <b>19</b> is a graphical representation the power function as a function of trial sound speed for an array of sensors in accordance with the present disclosure; and

FIG. <b>20</b> is a graphical representation the power function as a function of trial sound speed for an array of sensors in accordance with the present disclosure.

As part of the present disclosure, systems and methods are described to monitor the condition of a fluid within a hydraulic system. In certain implementations, a system and method are disclosed to measure the entrained air in an industrial hydraulic system. The system and method of this implementation includes the installation of a first acoustic pressure sensor in, or near, a first component within a hydraulic system and a second acoustic pressure sensor installed in, or near, to the of a second component of the hydraulic system, in which the first and second components are connected by a flexible hydraulic conduit. For the purposes of this disclosure, a flexible hydraulic conduit, also referred to as a flexible hydraulic hose, or simply a hydraulic hose, includes conduits that comprise composite material having one or more layers in which at least one layer contains an elastomer material, including any suitable type of rubber, any of which can be a tough elastic polymeric substance made from the latex of a tropical plant or made synthetically or a rubber-like substance and in which any of the at least one or more layers may contain reinforcing material such as steel wires or textile fibers such as fiberglass or Kevlar. For the purposes of this disclosure any substance with an elastic modulus of less than 1,000,000 psi and an elongation at yield of greater than 5% is defined as a rubber-like substance. A hydraulic conduit formed therefrom as described above is considered a flexible hydraulic hose or flexible hydraulic conduit. In general, the reinforcing layer(s) enable flexible hydraulic conduits to be capable of withstanding larger pressure differentials between the inside and the outside of the flexible hydraulic conduit, while maintaining flexibility in directions orthogonal to the centerline of the flexible conduit. Flexible hydraulic conduit is often used where connection between two elements of a hydraulic network is required, but where the path over which the connection is made not well defined, needs to change effective length or needs to vary in effective length with time as components to which they are attached move relative to one another. Flexible hydraulic conduits are widely used in mobile hydraulic systems. Flexible hydraulic conduits are well-suited for transferring hydraulic fluid over a range of pressures without transferring significant structural loads between two components. Flexible hydraulic conduit is contrasted to rigid conduits such as steel piping or metal piping and heavy plastic piping. Flexible hydraulic hose typically have minimum bend radius of on the order of 5 times the outer diameter of the flexible hydraulic conduit. The minimum bend radius is defined herein notionally as the minimum radius of curvature that a conduit can be bent without exceeding the elastic strain limit, or damaging, of any elements within the flexible conduit.

Most flexible hydraulic conduits have a specified minimum bend radius where applications in with the conduit is bend in a radius less than the minimum bend radius are not recommended due to likely premature failure. Flexible hydraulic conduits can also be contrasted to metal tubing. While metal tubing can be deformed to relatively small bend radii, the metal typically yields under deformation, thereby exceeding the elastic strain limit of the material, and resulting in the metal tubing deforming into an essentially rigid conduit deformed to a new shape.

It is noted that more than two sensors could be used as well, but, as an example, this disclosure describes at least one embodiment of the current invention which utilizes two acoustic sensors. The electronic output of the two acoustic sensors is monitored in a manner in which the temporal variations in the output of each sensor is recorded for each of the sensors forming what is typically referred to as a phased-array. In one embodiment, a two sensor phased-array, or simply “array”, is an acoustic array that has an acoustic aperture that spans at least a part of the length of the flexible hydraulic conduit and has an acoustic aperture length equal to the pathwise length of the conduit between the two acoustic pressure sensors comprising the two sensor array, or substantially the length of the flexible hydraulic conduit. The output of the acoustic pressure sensors comprise electric signals corresponding to, at least in part, pressure variations associated with essentially one dimensional sound waves propagating within the hydraulic piping network. The acoustic pressure sensors are electrically connected to a process module that utilizes the output of the two acoustic sensors to determine the process fluid sound speed within the acoustic aperture length of the acoustic array. With the sound speed known, and the static pressure within the line either known, measured, or estimated, and the density of the liquid and the composition of the gas phase either known, measured, or estimated, and the polytropic exponent either known, measured, or estimated, and the compliance introduced by elasticity of the conduit either known, measured, or estimated, Wood's equation can be used to determine the gas void fraction within the conduit connecting the two measurement locations. It has been discovered that the speed of sound can be effectively measured with the system described above to provide a practical and effective means of measuring the sound speed of a hydraulic fluid within hydraulic systems.

For sound propagating within a conduit for which the wavelength is large compared to both fluid inhomogeneities and the cross-sectional length scale of the conduit, Wood's equation [12,13] relates the sound speed, a<sub>mix</sub>, and density, ρ<sub>mix </sub>of a mixture consisting of “N” components to the volumetric phase fraction, φ<sub>i</sub>, density, ρ<sub>i </sub>and sound speed, a<sub>i </sub>of each component of the mixture. The elasticity of the conduit, given in Equation 1 below for a thin-walled, circular cross section conduit of diameter D and wall thickness of t and modulus of E, also influences the propagation velocity.

1
      
       
        ρ
        
         m
         ⁢
         i
         ⁢
         x
        
       
       ⁢
       
        a
        
         m
         ⁢
         i
         ⁢
         x
        
        2
       
      
     
     =
     
      
       
        
         ∑
          
        
        
         i
         =
         1
        
        N
       
       ⁢
       
        
         φ
         i
        
        
         
          ρ
          i
         
         ⁢
         
          a
          i
          2
         
        
       
      
      +
      
       
        D
        -
        t
       
       Et
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      1
     
     )
    
   
  
 


<br/>
Note, the last term represents the effect of the compliance of the conduit. Where the mixture density, ρ<sub>mix</sub>, is given by:

ρ
      
       m
       ⁢
       i
       ⁢
       x
      
     
     =
     
      
       
        ∑
         
       
       
        i
        =
        1
       
       N
      
      ⁢
      
       ρ
       i
      
      ⁢
      
       φ
       i
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      2
     
     )
    
   
  
 


<br/>
For bubbly liquids, Wood's equation can be expressed as a combination of a gas and liquid phase as follows:

1
      
       
        ρ
        
         m
         ⁢
         i
         ⁢
         x
        
       
       ⁢
       
        a
        
         m
         ⁢
         i
         ⁢
         x
        
        2
       
      
     
     =
     
      
       α
       
        
         ρ
         
          g
          ⁢
          a
          ⁢
          s
         
        
        ⁢
        
         a
         
          g
          ⁢
          a
          ⁢
          s
         
         2
        
       
      
      +
      
       
        1
        -
        α
       
       
        
         ρ
         
          l
          ⁢
          i
          ⁢
          q
         
        
        ⁢
        
         a
         
          l
          ⁢
          i
          ⁢
          q
         
         2
        
       
      
      +
      
       
        D
        -
        t
       
       Et
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      3
     
     )
    
   
  
 


<br/>
Where the mixture density is given by:
<br/>
description="In-line Formulae" end="lead"ρ<sub>mix</sub>=αμ<sub>gas</sub>+(1−α)μ<sub>liq</sub>  (Equation 4)description="In-line Formulae" end="tail"
<br/>
The mixture speed of sound can be expressed as a function of the gas void fraction and the fluid properties and properties of the conduit as follows:

a
      
       m
       ⁢
       i
       ⁢
       x
      
     
     =
     
      1
      
       
        
         ρ
         
          m
          ⁢
          i
          ⁢
          x
         
        
        ⁢
        
         (
         
          
           α
           
            
             ρ
             
              g
              ⁢
              a
              ⁢
              s
             
            
            ⁢
            
             a
             
              g
              ⁢
              a
              ⁢
              s
             
             2
            
           
          
          +
          
           
            1
            -
            α
           
           
            
             ρ
             
              l
              ⁢
              i
              ⁢
              q
             
            
            ⁢
            
             a
             
              l
              ⁢
              i
              ⁢
              q
             
             2
            
           
          
          +
          
           
            D
            -
            t
           
           
            E
            ⁢
            t
           
          
         
         )
        
       
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      5
     
     )

For cases in which the volumetrically-weighted compressibility of the gas phase is dominant source of compressibility of the mixture, which is typically a good approximation at near ambient conditions with gas void fractions >˜0.1%, the gas void fraction scales with the inverse of the square of the process fluid sound speed:

α
     ≅
     
      
       γ
       ⁢
       P
      
      
       
        ρ
        
         l
         ⁢
         i
         ⁢
         q
        
       
       ⁢
       
        a
        
         m
         ⁢
         i
         ⁢
         x
        
        2
       
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      6
     
     )

Where γ is the polytropic exponent governing the compressibility of the gas bubbles and P is the process pressure. The sound speed of the gas is expressed as a function of gas temperature, T, the gas constant, R, and the polytropic exponent γ.
<br/>
description="In-line Formulae" end="lead"<i>a</i><sub>gas</sub>=√{square root over (γ<i>RT</i>)}  (Equation 7)description="In-line Formulae" end="tail"
<br/>
The appropriate polytropic exponent depends on the frequency of the sound waves compared to a thermal relaxation frequency set by the bubble diameter and the thermal diffusivity of the gas [Fu, K. “Direct Numerical Study of Speed of Sound in Dispersed Air-Water Two-Phase Flow”, WaveMotion, Vol 98, November 2020]. For air bubbles, this polytropic exponent can range from isothermal conditions, γ=1.0, for low frequencies compared to the thermal relaxation frequency, to isentropic conditions, γ=1.4, for high frequencies compared to the thermal relaxation frequency. Note that polytropic exponent for gases undergoing isentropic compression and expansion is given by the ratio of the specific heat at constant pressure to the specific heat of air at constant volume.

Prior art systems and methods to determine the speed of sound of a fluid within a conduit have been limited to arrays of acoustic sensors positioned on conduits having a non-changing characteristic volumetric acoustic impedance (defined below and in Munjal). As will be disclosed in more detail hereinafter, changes in characteristic volumetric acoustic impedance can result in significant acoustic reflections that interfere with the ability of prior art systems to identify the one dimensional sound wave propagating within the hydraulic piping network. It has been discovered that, although reflections do impair the ability of array processing techniques to determine the speed of sound in a piping network compared to piping network without any reflections internal to the aperture of the acoustic array, the array processing techniques disclosed herein can be utilized effectively to determine the process fluid sound speed within acoustic arrays with apertures that span a section of flexible hydraulic conduit with surprising flexibility and in novel applications.

Referring to FIG. <b>2</b>, there is shown a cross sectional rendering of a quick disconnect coupling <b>20</b> of the prior art that can be part of a piping network. Quick disconnect coupling <b>20</b> includes male coupling half <b>21</b> attached to a first hydraulic hose <b>22</b> and female coupling half <b>23</b> attached to a second hydraulic hose <b>24</b>. As shown, hydraulic fluid <b>25</b> can flow through quick disconnect coupling <b>20</b> in the coupled position. As is known, quick disconnect couplings <b>20</b> have several components that serve to shut-off the flow area when the connector is disconnected, and allow fluid connectivity when connected. As part of the current disclosure, and assuming a quick disconnect fitting is installed between two sections of hydraulic hose to form a piping network, the internal cross sectional area changes over the length of the piping network from the diameter of first hydraulic hose <b>22</b>, through the internal diameter variations associated with the quick disconnect coupling <b>20</b> and the diameter of second hydraulic hose <b>24</b>. The cross sectional area within quick disconnect coupling <b>20</b> varies and differs significantly—and is typically significantly reduced—from the cross sectional area of the hydraulic hoses <b>22</b>, <b>24</b>. It is noted that embodiments of this disclosure are also applicable to other types of connectors or fittings used to terminate hydraulic hose and provide fluid communication to other hoses or other components in a hydraulic network such as pumps, reservoirs, manifolds, etc.

Although used merely as an example, the reduced cross section area of quick disconnect coupling <b>20</b>, as well as other type of connectors, such as threaded and or crimped connectors, result in a pressure drop in the hydraulic fluid <b>25</b> across the connector pair <b>21</b>, <b>23</b>. This pressure drop is primarily due to the acceleration of oil <b>25</b> through the smaller cross sectional areas of quick disconnect coupling <b>20</b>. In addition to creating a pressure loss in the system, cross sectional area change produces a change in the characteristic volumetric acoustic impedance of the piping network. The pressure loss can result in changes in the gas void fraction of the hydraulic fluid due to the introduction of outgassing due to the pressure drop or simply additional outgassing and expansion of gas that may already be present in the hydraulic fluid. Increases in gas void fraction typically result in significant changes in the characteristic volumetric acoustic impedance associated with the process fluid within the piping network. This change in cross sectional area, and pressure loss, and changes in gas void fraction, can result in significant characteristic volumetric acoustic impedance and therefore significant acoustic reflections, and associated transmission loss, for a one dimensional sound wave propagating within the oil of a hydraulic piping network.

Referring to Equation 8 below, the reflection coefficient R, defined as the ratio of a reflected one dimensional acoustic wave B associated with an incident acoustic wave of amplitude A incident upon a simple area change from first area S<b>1</b> to a second area S<b>2</b>:

R
      ≡
      
       B
       A
      
     
     =
     
      
       
        1
        -
        
         
          S
          2
         
         
          S
          1
         
        
       
       
        1
        +
        
         
          S
          2
         
         
          S
          1
         
        
       
      
      =
      
       
        
         S
         1
        
        -
        
         S
         2
        
       
       
        
         S
         1
        
        +
        
         S
         2
        
       
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      8
     
     )

It should be noted that in hydraulic piping networks comprised of sections of hoses and connectors (or fittings), area ratios of S<b>2</b>/S<b>1</b>=0.5 or smaller are not uncommon. An area ratio of 0.5 results in a relatively significant reflection coefficient of 0.33, indicating that at such an area change, ⅓ of the incident acoustic pressure field is reflected back into the hose. It is also noted that this estimate is offered as an example, and does not include effects that would serve only serve to increase the transmission loos and reflections such as an increase in gas void fraction that typically accompany area restriction.

As part of the present disclosure, the effects of these reflections are modelled utilizing one-dimensional acoustics. For one-dimensional acoustic pressure fields for which the speed of sound is much larger than the flow velocity (i.e. M<sub>x</sub>=U<sub>x</sub>/a<<1 where M<sub>x </sub>is the Mach number, U<sub>x </sub>is the flow velocity and a is the speed of sound), the acoustic pressure and the acoustic axial velocities perturbations of the one-dimensional acoustic waves can be expressed as a function of position and time as follows:
<br/>
description="In-line Formulae" end="lead"<i>P</i><sub>i</sub>(<i>x,t</i>)=<i>A</i><sub>i</sub><i>e</i><sup>i(ωt−kx)</sup><i>+B</i><sub>i</sub><i>e</i><sup>i(ωt+kx) </sup>and <i>U</i><sub>i</sub>(<i>x,t</i>)=(<i>A</i><sub>i</sub><i>e</i><sup>i(ωt−kx)</sup><i>−B</i><sub>i</sub><i>e</i><sup>i(wt+kx)</sup><i>/ρc</i>  (Equation 9)description="In-line Formulae" end="tail"

Where A<sub>i </sub>and B<sub>i </sub>represent the complex amplitudes of the right and left (or forward and backward) travelling pressure waves respectively travelling within the i<sup>th </sup>region in which the characteristic volumetric acoustic impedance is essentially constant. Additionally, ω is the temporal frequency in rad/sec, k=ω/a<sub>mix</sub>=2π/λ, is the wave number, a<sub>mix </sub>is the speed of sound, and where λ is the acoustic wavelength.

In modelling acoustic networks which contain area changes, the effect of area changes are typically modelled by assuming that right and left travelling waves exist in regions upstream and downstream of an area change, and then relating the complex amplitudes of the pressure fields upstream and downstream of the area discontinuity by applying momentum and continuity conditions across the area change as commonly used in the art and as described in (Munjal, M. L. Acoustics of Ducts and Mufflers, ISBN 0-471-84738-0)

With reference to Munjal disclosed herein above, the acoustic impedance (z) of an acoustic wave propagating in a free space is typically defined as the ratio of the acoustic pressure perturbation (p) to the acoustic velocity perturbation (u). This ratio is a property of the fluid and given by:

z
      ≡
      
       p
       u
      
     
     =
     
      ρ
      ⁢
      c
     
    
   
   
    
     Equation
     ⁢
        
     10

Where ρ is the density of the fluid and c is the speed of sound of one dimensional acoustic waves.

For one-dimensional acoustics propagating within a duct, the ratio of the acoustic pressure (p) in a one-dimensional acoustic wave to the acoustic volumetric velocity (uS), where S is the cross sectional area of the duct, with reference to Munjal again, is perhaps a more relevant characteristic of the one-dimensional acoustic properties of a fluid within a duct. This ratio can be defined as the characteristic volumetric impedance of a fluid within duct (Y), where Y is defined as:

Y
      ≡
      
       p
       
        u
        ⁢
        S
       
      
     
     =
     
      
       ρ
       ⁢
       c
      
      S
     
    
   
   
    
     Equation
     ⁢
        
     11

Note that for a fluid with constant density and sound speed, a 20% reduction in cross sectional area which is common in many hydraulic system would result is a 25% increase in the characteristic volumetric impedance within a duct. Note additionally that the change in compliance of the conduit, as described by Wood's equation, also changes propagation speed of the one-dimensional sound wave, and this results a change in the effective characteristic volumetric impedance of a fluid within duct (Y), and will, in general, result in reflections. For example, an acoustic wave propagating in a fluid in a steel conduit would experience a change in effective characteristic volumetric impedance, and a reflection, at an interface with a flexible hydraulic conduit

Consider the piping network <b>45</b> depicted in FIG. <b>9</b> as a simplified model of a hydraulic hose <b>48</b> connecting two components in a piping network <b>45</b>. The acoustic model has three regions, the first component inlet pipe <b>46</b>, a hydraulic hose <b>48</b>, and the second component outlet pipe <b>50</b>. The coupling <b>47</b> is considered as Region <b>1</b> having a length of ΔX and a cross sectional area S<sub>1</sub>; the length of hydraulic hose <b>48</b> is considered as Region <b>2</b> having a length of L and a cross sectional area S<sub>2 </sub>and the coupling <b>49</b> is considered as Region <b>3</b> having a length of ΔX and a cross sectional area S<sub>3</sub>. For purposes of this example, the relative coordinate system comprises transducer <b>52</b> at position X<sub>1</sub>=−ΔX; the interface between coupling <b>49</b> and hydraulic hose <b>48</b> at position X<sub>2</sub>=0; the interface between coupling <b>47</b> and hydraulic hose <b>48</b> at position X<sub>3</sub>=L; and transducer <b>52</b> at position X<sub>4</sub>=L+ΔX. The component regions in general represent components within a hydraulic system and may specifically represent any elements in a hydraulic network including for example connectors, pumps, filters, reservoirs, manifolds, or actuators

The pressure fields in Region <b>1</b> and Region <b>3</b> can be related to each other by applying pressure (momentum) and mass flow (continuity) at each of the interfaces, with the first interface at x=0,
<br/>
description="In-line Formulae" end="lead"<i>P</i><sub>x=0</sub><sub>−</sub><i>=P</i><sub>x=0</sub><sub>+</sub> and <i>S</i><sub>1</sub><i>U</i><sub>x=0</sub><sub>−</sub><i>=S</i><sub>2</sub><i>U</i><sub>x=0</sub><sub>+</sub>  (Equation 12)description="In-line Formulae" end="tail"

    
    
        and the second interface at x=L (length of flexible hose <b>48</b>),
<br/>
description="In-line Formulae" end="lead"<i>P</i><sub>x=L</sub><sub>−</sub><i>=P</i><sub>x=L</sub><sub>+</sub> and <i>S</i><sub>2</sub><i>U</i><sub>x=L</sub><sub>−</sub><i>=S</i><sub>3</sub><i>U</i><sub>x=1</sub><sub>+</sub>  (Equation 13)description="In-line Formulae" end="tail"

        Note this analysis neglects any effects associated with the change in compliance of the conduits at the interfaces.
        Applying these relationships, the pressure fields in each of the regions can be related as follows:

(
     
      Equation
      ⁢
         
      14
     
     )
    
   
  
 




 
  
   
    [
    
     
      
       
        -
        
         e
         
          ikx
          2
         
        
       
      
      
       
        e
        
         -
         
          ikx
          2
         
        
       
      
      
       
        e
        
         ikx
         2
        
       
      
      
       0
      
     
     
      
       
        -
        
         e
         
          i
          ⁢
          k
          ⁢
          
           x
           2
          
         
        
       
      
      
       
        
         -
         
          
           s
           2
          
          
           s
           1
          
         
        
        ⁢
        
         e
         
          
           -
           i
          
          ⁢
          k
          ⁢
          
           x
           2
          
         
        
       
      
      
       
        
         
          s
          2
         
         
          s
          1
         
        
        ⁢
        
         e
         
          i
          ⁢
          k
          ⁢
          
           x
           2
          
         
        
       
      
      
       0
      
     
     
      
       0
      
      
       
        -
        
         e
         
          
           -
           i
          
          ⁢
          k
          ⁢
          
           x
           3
          
         
        
       
      
      
       
        e
        
         i
         ⁢
         k
         ⁢
         
          x
          3
         
        
       
      
      
       
        -
        
         e
         
          
           -
           i
          
          ⁢
          k
          ⁢
          
           x
           3
          
         
        
       
      
     
     
      
       0
      
      
       
        -
        
         e
         
          
           -
           ik
          
          ⁢
          
           x
           3
          
         
        
       
      
      
       
        e
        
         i
         ⁢
         k
         ⁢
         
          x
          3
         
        
       
      
      
       
        
         
          s
          3
         
         
          s
          2
         
        
        ⁢
        
         e
         
          
           -
           i
          
          ⁢
          k
          ⁢
          
           x
           3
          
         
        
       
      
     
    
    ]
   
   ⁢
   
    {
    
     
      
       
        B
        1
       
      
     
     
      
       
        A
        2
       
      
     
     
      
       
        B
        2
       
      
     
     
      
       
        A
        3
       
      
     
    
    }
   
  
  =
  
   {
   
    
     
      
       
        A
        1
       
       ⁢
       
        e
        
         -
         
          ikx
          2
         
        
       
      
     
    
    
     
      
       
        -
        
         A
         1
        
       
       ⁢
       
        e
        
         
          -
          i
         
         ⁢
         k
         ⁢
         
          x
          2
         
        
       
      
     
    
    
     
      
       
        B
        3
       
       ⁢
       
        e
        
         i
         ⁢
         k
         ⁢
         
          x
          3
         
        
       
      
     
    
    
     
      
       
        B
        3
       
       ⁢
       
        
         s
         3
        
        
         s
         2
        
       
       ⁢
       
        e
        
         i
         ⁢
         k
         ⁢
         
          x
          3
         
        
       
      
     
    
   
   }

Using these relationships, pressures at the locations of sensors <b>52</b>, <b>54</b> can be simulated and the simulated pressures can be used as input to beam forming algorithms to assess the ability of the beamforming algorithms to determine the speed of sound based on these simulated measurements for a range of flow path geometries.

Specifically, for an acoustic pressure field with a right traveling wave (in the positive X direction) in Region <b>1</b> with complex amplitude A<sub>1</sub>, and a left traveling wave (in the negative X direction) in Region <b>1</b> with a complex amplitude of B<sub>1</sub>, and a right traveling wave (in the positive X direction) in Region <b>3</b> with complex amplitude A<sub>3</sub>, and a left traveling wave (in the negative X direction) in Region <b>3</b> with a complex amplitude of B<sub>3</sub>, the measured pressures at pressure transducers, <b>52</b> and <b>54</b> normalized by the amplitude of A<sub>1</sub>, are given by:
<br/>
description="In-line Formulae" end="lead"<i>p</i><sub>52</sub>(ω)/<i>A</i><sub>1</sub><i>=e</i><sup>i(ωt−kx</sup><sup>1</sup><sup>)</sup><i>+B</i><sub>1</sub><i>/A</i><sub>1</sub><i>e</i><sup>i(ωt−kx</sup><sup>1</sup><sup>)</sup>  Equation 15description="In-line Formulae" end="tail"
<br/>
description="In-line Formulae" end="lead"<i>p</i><sub>54</sub>(ω)/<i>A</i><sub>1</sub><i>=A</i><sub>3</sub><i>/A</i><sub>1</sub><i>e</i><sup>i(ωt−kx</sup><sup>4</sup><sup>)</sup><i>+B</i><sub>3</sub><i>/A</i><sub>1</sub><i>e</i><sup>i(ωt−kx</sup><sup>4</sup><sup>)</sup>  Equation 16description="In-line Formulae" end="tail"

Where ω is the temporal frequency in radians/second, t is time in seconds, k is the wavenumber, where

k
   =
   
    
     ω
     
      a
      
       m
       ⁢
       i
       ⁢
       x
      
     
    
    =
    
     
      2
      ⁢
      π
     
     λ
    
   
  
  ,
 


<br/>
where a<sub>mix </sub>is the mixture sound speed and λ is the wavelength and where the complex amplitudes of B<sub>1 </sub>and A<sub>3 </sub>are given terms of A<sub>1 </sub>and B<sub>3 </sub>by Equation 14. Note, for clarity, A<sub>i </sub>is the complex amplitude of the right travelling wave in the i<sup>th </sup>region, and B<sub>i </sub>is the complex amplitude of the left traveling wave in the i<sup>th </sup>region. The relationships of Equations 15 and 16 represent Fourier coefficients for each frequency of the simulated pressures measured at the locations of the pressure transducers <b>52</b> and <b>54</b>. Performing the simulation in this manner results in a general condition in which can model conditions for which there are arbitrary levels of right traveling waves, A<sub>1</sub>, in Region <b>1</b> and left traveling waves, B<sub>3</sub>, in each Region <b>3</b> of the flow field.

Referring now to FIGS. <b>3</b>, <b>4</b>A and <b>4</b>B, there is shown an example of the effect of area discontinuities on the simulated pressure at the locations of two transducers. With specific reference to FIG. <b>3</b>, there is shown a schematic of a hydraulic piping network having a Region <b>1</b> with a cross section area S<b>1</b> and an acoustic pressure sensor P<b>1</b> positioned at a distance −ΔX from an end thereof, a Region <b>2</b> comprised of a flexible hydraulic hose with a cross section area S<b>2</b> and having a length L and having a Region <b>3</b> with a cross section area S<b>3</b> and an acoustic pressure sensor P<b>2</b> positioned at a distance ΔX from an end thereof. It should be understood by those skilled in the art that the length of the acoustic aperture of FIG. <b>3</b> is the distance between P<b>1</b> and P<b>2</b> and is equal to L+2(ΔX). FIGS. <b>4</b>A and <b>4</b>B show the magnitude and phase of the pressure simulated at each transducer PP<b>1</b>, PP<b>2</b> for a unit amplitude right traveling wave in Region <b>1</b>, i.e, A<sub>1</sub>=1 and no sound propagating to the left in Region <b>3</b>, i.e. B<sub>3</sub>=0. For clarity, B<sub>3</sub>=0 implies both no reflections at the termination of Region <b>3</b>, i.e. anechoic, and no sources of sound that would generate sound propagating to the left in Region <b>3</b>, or some combination of the two that results in B<sub>3</sub>=0. The sound speed of the fluid in the simulation is 600 ft/sec. ΔX is 1 inch, and L is 60 inches, and S<b>1</b>=S<b>2</b>=S<b>3</b> for the simulation of FIGS. <b>3</b> and <b>4</b>. For this configuration the sound field is propagating in a constant amplitude right traveling wave through the simulation region, and with the phase of sensor P<b>2</b> lagging sensor P<b>1</b> linear with frequency, consistent with a pure time associated with a pressure field consistent with a sound field with a constant amplitude, broad band acoustic waves propagating in the right (positive X) direction.

FIGS. <b>5</b> and <b>6</b> show the magnitude and phase of each pressure transducer P<b>1</b> and P<b>2</b> for the same configuration depicted schematically in FIG. <b>3</b>, but with a 20× area reduction from Region <b>1</b> to Region <b>2</b>, and a 20× area increase from Region <b>2</b> to Region <b>3</b>. As shown, the magnitude and phase relationship between the two sensors is quite different from that shown in FIGS. <b>4</b>A and <b>4</b>B, with the area changes at either end of the hose (modeled as Region <b>2</b>) setting up an acoustically resonant cavity within the hose. The resonance is indicated by the peak in the pressure response of a transducer P<b>2</b> and the minimum in the response of transducer P<b>1</b>. This resonance corresponds to the ½ wavelength resonance of Region <b>2</b>, and occurs at 60 Hz where:
<br/>
description="In-line Formulae" end="lead"<i>f*λ=a</i><sub>mix</sub>  (Equation 17);description="In-line Formulae" end="tail"
<br/>
description="In-line Formulae" end="lead"λ=2<i>L</i>  (Equation 18); anddescription="In-line Formulae" end="tail"

f
     =
     
      
       
        a
        
         m
         ⁢
         i
         ⁢
         x
        
       
       
        2
        ⁢
        L
       
      
      =
      
       
        
         600
         ⁢
            
         ft
         /
         sec
        
        
         2
         *
         5
         ⁢
            
         ft
        
       
       =
       
        60
        ⁢
           
        Hz
       
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      19
     
     )
    
   
  
 


<br/>
For this configuration, the area changes significantly reduce the propagation of sound through the acoustic aperture of the array for most frequencies except for frequencies near this resonant frequency, at which the sound propagates through the acoustic aperture minimally impeded.

Since area changes and changes in gas void fraction associated with the pressure drop due to area restrictions and, to some degree, increased compliance of hydraulic hoses can set up strong reflections at the entrance and exit of hydraulic hoses, it is of interest to determine if the simulated measured pressures from an acoustic array whose acoustic aperture contains a transition to and from a flexible hydraulic hose, can be interpreted in terms of the process fluid sound speed utilizing beamforming algorithms. It is important to recognize that the this analysis only considers reflections due to area changes, and does not consider the potentially larger effects due to the potential effect that the change in gas void fraction of process fluid due to pressure drop through area changes could have on the characteristic volumetric acoustic impedance of the process fluid. As such, this analysis is offered to demonstrate how a simplified model including only the effect of area changes can impair the performance of a beam forming techniques on representative application scenarios.

Beamforming, as used herein, involves defining a steering vector that accounts for an expected phase shift among the measured, or in this case simulated, pressures associated with a trial process fluid sound speed. In the prior art, beamforming algorithms for determining flow parameters, such as flow velocity and process fluid speed of sound, have been applied to measurements from acoustic pressure sensors for which the cross sectional area of the fluid conduit within the aperture of the array is constant, and for which there are not significant internal acoustic reflections within the array, nor for which there was significant sound generation within the array.

The steering vector for data measured from pressure transducers P<b>1</b>, P<b>2</b> of FIG. <b>3</b> (and <b>52</b>, <b>54</b> of FIG. <b>9</b>) is given by the following:

E
     =
     
      {
      
       
        
         
          e
          
           
            -
            i
           
           ⁢
           k
           ⁢
           
            x
            1
           
          
         
        
       
       
        
         
          e
          
           
            -
            i
           
           ⁢
           k
           ⁢
           
            x
            4
           
          
         
        
       
      
      }
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      20
     
     )
    
   
  
 


<br/>
Where k is defined as the wave number,

k
   =
   
    ω
    c
   
  
  ,
 


<br/>
where c is the speed of sound and ω is the frequency in radians/sec. In this formulation of the steering vector, positive wave numbers are associated with waves traveling in the positive “X” direction (from left to right) and negative wave numbers are associated with waves traveling in the negative “X” direction (from right to left).

The cross spectral density matrix is composed of the cross spectral densities of the measured or simulated pressures at each location:

CSD
     =
     
      [
      
       
        
         
          P
          
           1
           ⁢
           1
          
         
        
        
         
          P
          
           1
           ⁢
           4
          
         
        
       
       
        
         
          P
          
           4
           ⁢
           1
          
         
        
        
         
          P
          
           4
           ⁢
           4
          
         
        
       
      
      ]
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      21
     
     )
    
   
  
 


<br/>
Where P<sub>ij</sub>=P<sub>i</sub>*P*<sub>j</sub>, where P<sub>i </sub>and P*<sub>j </sub>are the Fourier transforms of the pressures at location i and the complex conjugate of the Fourier transform at location j.

Following techniques described in D. H. Johnson and D. E. Dudgeon. <i>Array Signal Processing, Concepts and Techniques</i>. PTR Prentice-Hall, Upper Saddle River, NJ, 1993, the beamforming optimization process of the current disclosure involves adjusting the steering vector, which is a function of the speed of sound of the process fluid, to maximize the power associated with a given steering vector. The power of the array is given by the following:
<br/>
description="In-line Formulae" end="lead"<i>P=E</i><sup>T</sup><i>[CSD]E</i>  (Equation 22)description="In-line Formulae" end="tail"
<br/>
Where E<sup>T </sup>is the conjugate transpose of the steering vector, E.

FIG. <b>7</b> is a graphical representation of an example of determining the speed of sound from an array of two pressure transducers using beam forming techniques utilizing simulated data for the configuration described above as a function of the ratio of the area contraction, with further reference to FIG. <b>9</b>, at couplings <b>47</b> (Region <b>1</b>), <b>49</b> (Region <b>2</b>) and area expansion entering and exiting the hose <b>48</b> (Region <b>2</b>) section.

In FIG. <b>7</b>, area change ratios of 0.05, 0.10, 0.25, 0.5 and 1 are shown wherein the area change ratio of 1 comprises no area change. Inventively, and as shown, although the configuration without the area change (area change ratio of 1) provides the most well defined determination of sound speed within the array, the beam forming techniques are shown to provide an accurate estimate of the process fluid sound speed under the idealized assumptions of the analysis for a wide range of area changes between region <b>1</b> and <b>2</b> and regions <b>2</b> and <b>3</b>, a model which is offered as representative of a hydraulic hose with fittings on either end with pressure transducers installed in each fitting.

As indicated by FIG. <b>7</b>, the presence of the changes in the characteristic volumetric acoustic impedance associated with the area discontinuities does degrade the ability of the beam forming techniques to identify the speed of sound of the process fluid compared to an array without any changes in the characteristic volumetric acoustic impedance. The implications of this degradation depend on the signal to noise environment of the sensors, and the degree to which other coherent signals within the array are present. The current disclosure inventively leverages several aspects of the current embodiment to optimize the performance of the beam forming methods to determine the process fluid sound speed under conditions within which the characteristic volumetric acoustic impedance varies within the array. These inventive aspects are developed in more detail below and include: 1) measuring the speed of sound within a flexible conduit minimizes any coherent structural waves that are generally readily transmitted through rigid conduits (wherein these structural waves can include bending wave, torsional waves, shear waves, compression waves and others) and where these propagating structural waves result in coherent signals within multiple pressure transducers within the array due to, for example, cross talk in the form of sensitivity of pressure transducers to acceleration; 2) the relatively long length of typical hydraulic hoses enables longer acoustic apertures and thereby the use of lower frequency sound to determine the process fluid speed of sound (wherein low frequency sound is typically present at higher amplitude than higher frequency sound which attenuates more quickly in bubbly liquids and offers improve signal to noise); 3) the long length of hydraulic hoses compared to the diameter of the hydraulic hose typically ensures that the length of the acoustic aperture of the acoustic array exceeds the effective coherent length of vortical disturbances, minimizes the degree to which coherent pressure disturbance due to vortical disturbances are measured at multiple pressure sensors within the array; and 4) porting directly into the process flow lines at the fittings enables a direct measurement of the unsteady pressure within the flow lines, which minimizes the amount of structural cross talk contained in the pressure signals compared to, for example, sensors designed to measure unsteady pressure within an effectively rigid conduit utilizing a measurement of the strain in the conduit itself.

In real world applications of array processing, various noise sources and signals from competing coherent disturbances can serve to impair the ability of beamforming algorithms to interpret the output of a sensor array to determine the desired properties of a propagating sound field. As indicated by the analysis disclosed herein above, reflections produced within the array can impair the interpretation of the process fluid sound speed. Noise sources can include electrical noise, signal cross talk, etc. Other sources of coherent disturbances that can impair the ability of a beamforming algorithm to determine a process fluid sound speed include coherent vortical disturbances and coherent structural vibrations picked up by the pressure sensors, as discussed above.

Heretofore, gas void fraction meters that utilize array processing techniques to measure a process fluid sound speed to determine the gas void faction of a process fluid of the prior art utilize numerous sensors within a linear array to help discern the desired information, i.e. the speed of sound, by interpreting the output of an array of sensors measuring the strain within an essentially rigid conduit in the presence of noise sources and other coherent disturbances on an array. An example from the prior art, is SONARtrac® commercially available from CiDRA Corporation. The SONARtrac® product utilizes 8 strain based sensors in their commercial clamp-on strain-based sensors that measure the dynamic strain in an essentially rigid conduit to determine the speed at which one dimensional waves propagate within a process fluid within an essentially rigid conduit. One drawback to such prior art systems is that the strain-based system requires an essentially rigid conduit and would not work on for flexible hydraulic hoses.

The presence of coherent pressure variations due to vortical disturbances within piping networks is well established. For an array of sensors measuring pressure variations over an aperture length for which the vortical disturbances remain coherent, the vortical disturbances would serve to confound any systems attempting to measure the process fluid sound speed using similar frequency ranges. Vortical disturbances within conduits typically have a coherence length on the order of 10 times the diameter of the conduit. Vortical disturbances typically have frequencies on the order of 1 to 10 times or higher times the ratio of the mean velocity divided by the diameter. Depending on the diameter and flow rates and the acoustic environment, vortical disturbances can often be the largest source of low frequency unsteady pressure variations within a conduit, often exceeding acoustic pressure variations. By utilizing arrays with sensor spacing that is long compared to 10 times the diameter of the conduit, embodiments of the current disclosure can utilize low frequency acoustics without picking up coherent vortical disturbances that are often present at low frequencies.

Depending on the signals sought, the signal to noise ratio, and other considerations, SONAR arrays of the prior art towed behind vessels can have >1000 sensors in a linear array with an aperture of >1000 metes https://en.wikipedia.org/wiki/Towed_array_sonar. The large number of sensors in often driven by the number, type, and prevalence of multiple coherent signals picked-up by the array. The approach disclosed herein leverages advantages of including a hydraulic hose within the aperture of the array to improve signal to noise and enable effects determination of a process fluid sound speed utilizing only two sensors.

It is known that process fluids within piping networks include, among other things, coherent acoustic waves, coherent vortical structures, and coherent propagating structural disturbances. Implementations described in this disclosure are particularly well-suited to minimize any effects of coherent vortical structures and coherent propagating structural disturbances on its ability to effectively determine the process fluid sound speed with a hydraulic system. Namely, although the hydraulic hoses are flexible lengthwise, hydraulic hoses are effective at transmitting acoustic pressure pulsations and not very effective at transmitting other types of competing coherent signals. Therefore it is an aspect of the present disclosure that the flexible hydraulic hose within the piping network is configured to preferentially, with respect to the coherent acoustic waves, reduce the coherence between the signals measured by a pair of acoustic pressure sensors associated with the coherent vortical structures, and coherent propagating structural disturbances.

It should be appreciated by those skilled in the art that Wood's equation can be used to analyze the effect of a change in the acoustic compliance of a conduit on the speed of sound within that conduit:

1
      
       
        ρ
        
         m
         ⁢
         i
         ⁢
         x
        
       
       ⁢
       
        a
        
         m
         ⁢
         i
         ⁢
         x
        
        2
       
      
     
     =
     
      
       
        
         ∑
          
        
        
         i
         =
         1
        
        N
       
       ⁢
       
        
         φ
         i
        
        
         
          ρ
          i
         
         ⁢
         
          a
          i
          2
         
        
       
      
      +
      
       
        D
        -
        t
       
       Et
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      23
     
     )
    
   
  
 


<br/>
The acoustic compliance of a conduit can be defined as the change in cross sectional area (normalized by the nominal cross sectional area) per change in acoustic pressure. For a circular duct of constant thickness, diameter, and modulus of elasticity, the acoustic compliance can be expressed as:

σ
      
       c
       ⁢
       onduit
      
     
     ≡
     
      
       D
       -
       t
      
      Et
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      24
     
     )
    
   
  
 


<br/>
Where D is the diameter of the conduit, t is the wall thickness of the conduit and E is modulus of elasticity of the conduit.
<br/>
And the compliance of the fluid mixture within the conduit can be expressed as:

σ
      
       m
       ⁢
       i
       ⁢
       x
      
     
     ≡
     
      1
      
       
        ρ
        
         m
         ⁢
         i
         ⁢
         x
        
       
       ⁢
       
        a
        
         m
         ⁢
         i
         ⁢
         x
        
        2
       
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      25
     
     )
    
   
  
 


<br/>
Where ρ<sub>mix </sub>is the density of the fluid mixture and a<sub>mix </sub>is the speed of sound of the fluid mixture.
<br/>
For the same fluid, the speed of sound change associated with a change in the conduit compliance between two conduits can be approximated as:

a
      
       m
       ⁢
       i
       ⁢
       
        x
        2
       
      
     
     =
     
      
       a
       
        m
        ⁢
        i
        ⁢
        
         x
         1
        
       
      
      
       sqrt
       ⁡
       (
       
        1
        +
        
         
          ρ
          
           m
           ⁢
           i
           ⁢
           x
          
         
         ⁢
         
          
           a
           
            m
            ⁢
            i
            ⁢
            
             x
             1
             2
            
           
          
          (
          
           
            σ
            
             conduit
             2
            
           
           -
           
            σ
            
             conduit
             1
            
           
          
          )
         
        
       
       )
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      26
     
     )
    
   
  
 


<br/>
The reflection coefficient for a one dimensional acoustic wave incident upon a change in the compliance of the conduit can be expressed, as:

R
     ≡
     
      
       
        a
        
         m
         ⁢
         i
         ⁢
         
          x
          2
         
        
       
       -
       
        a
        
         m
         ⁢
         i
         ⁢
         
          x
          1
         
        
       
      
      
       
        a
        
         m
         ⁢
         i
         ⁢
         
          x
          2
         
        
       
       +
       
        a
        
         m
         ⁢
         i
         ⁢
         
          x
          1
         
        
       
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      27
     
     )
    
   
  
 


<br/>
Where, assuming the compliance of the pipe is small compared to the compliance of the mixture,

σ
       
        conduit
        2
       
      
      
       σ
       mix
      
     
     ≪
     1
    
   
   
    
     (
     
      Equation
      ⁢
         
      28
     
     )
    
   
  
 




 
  
   
    σ
    
     conduit
     1
    
   
   
    σ
    mix
   
  
  ≪
  1
 


<br/>
The reflection coefficient can be written as:

R
     ≡
     
      
       -
       
        1
        4
       
      
      ⁢
      
       (
       
        
         
          σ
          
           conduit
           2
          
         
         -
         
          σ
          
           conduit
           1
          
         
        
        
         σ
         mix
        
       
       )
      
     
    
   
   
    
     (
     
      Equation
      ⁢
         
      29
     
     )
    
   
  
 


<br/>
For low pressure process fluids such as fluid in the return line of hydraulic system, even small amounts of entrained gas result in large mixture compliances, and therefore, in most cases, relatively small reflection coefficients are found at the transition from a relatively rigid conduit into a hydraulic hose for fluid with non-zero amounts of entrained gas

For example, assuming a pressure of 100 psi, the reflection coefficient associated with an one-dimensional acoustic wave propagating in steel conduit of 1 inch diameter and 0.2 inches thick and elastic modulus of 30 million psi, encountering a change in conduit compliance associated with a PVC pipe of the same dimensions but with a modulus of 1/100<sup>th </sup>that of steel, the reflection coefficient associated with change in the compliance of the conduit would be R<0.2 for a typical hydraulic fluid with >0.05% entrained air by volume. For larger amount of entrained air by volume, or for lower pressures, the reflection coefficient would be lower. For smaller amount of entrained air by volume, or for higher pressures, the reflection coefficient would be larger.

Thus, although reflections of one dimensional acoustics will, in general, occur in aerated and non-aerated hydraulic fluids at the transition from rigid conduits (with low acoustic compliances) to flexible hydraulic hoses (with higher acoustic compliances) due primarily to changes in cross section area and changes in gas void fraction due to pressure drop, and to a lesser extend due to changes in the compliance of the conduit, the current disclosure teaches that acoustics are typically sufficiently well-transmitted though changes in the characteristic volumetric impedance associated with transitions into and out of flexible hydraulic hoses to make determine at the process fluid sound speed. Moreover, there are specific aspects of the current invention that promote the ability to utilize a low number of pressure sensors to enable a determination of the process fluid sound speed. These include 1) the length-wise bending flexibility and length-wise torsional compliance of hydraulic hoses effectively prevents hydraulic hoses from effectively transmitting structural vibrations from one end of the hose to the other end of the hose. As such, hydraulic hoses serve as effective vibration isolators within a piping network. Specifically, by mounting the transducers on a piping network that spans a section of flexible hose, this implementation of the current disclosure effectively filters out coherent structural vibrations from one sensor to the other. 2) Additionally, hydraulic hoses within hydraulic systems typically have length to diameter ratios of >10. The coherence of vortical disturbances in a process fluid flowing within a conduit decreases with length. Thus, for applications in which the length to diameter ratio of hose contained within the acoustic aperture of a sensor array is long, for example greater than 10, the likelihood of vortical disturbances significantly impairing the interpretation of the process fluid sound speed is quite low, and decreases further with flexible hydraulic hoses that have larger length to diameter ratios; and 3) In further addition, long length hoses promote the ability of determining the process fluid sound speed because long aperture enable the use of typically higher amplitude, better signal to noise conditions, or low frequency waves compared to prior art methods that typical utilized much shorter array apertures. the long length of hydraulic hoses

An implementation of a fluid measuring system of the current disclosure can be seen with reference to hydraulic system <b>30</b> of FIG. <b>8</b>. FIG. <b>8</b> is a schematic drawing of hydraulic system <b>30</b> comprised of reservoir <b>31</b> coupled to pump <b>32</b> by hydraulic hose <b>33</b>. of an embodiment of the invention. Hydraulic hose <b>33</b> has a constant cross-sectional area along its hose length and includes reservoir coupling <b>34</b> positioned on a first end portion to attach to the liquid outlet of reservoir <b>31</b> and pump coupling <b>35</b> positioned on a second end portion to attach to the suction side of pump <b>32</b>. Hydraulic system <b>30</b> further includes fluid monitoring system <b>37</b> comprised a first acoustic pressure sensor <b>38</b>, a second acoustic pressure sensor <b>39</b> and a processing unit <b>40</b>. First acoustic pressure sensor <b>38</b> is electrically coupled to processing unit <b>40</b> by wire <b>41</b> and second acoustic pressure sensor <b>39</b> is electrically coupled to processing unit <b>40</b> by wire <b>42</b>. As shown, first acoustic pressure sensor <b>38</b> is installed in oil reservoir <b>31</b> in close proximity to the liquid outlet and configured to sense the acoustic pressures in reservoir near fitting <b>34</b>. It should be appreciated by those skilled in the art that acoustic pressure sensor <b>38</b> could also be installed on reservoir coupling <b>34</b>. Second acoustic pressure sensor <b>39</b> is installed on the suction side of pump <b>32</b> but could be installed in pump coupling <b>35</b>. Hydraulic hose <b>33</b> could include a filter (not shown) or the filter, if present, could be considered another component of hydraulic system <b>30</b>, and a pressure transducer could be installed in or near the filter. The acoustic pressure transducers <b>38</b>, <b>39</b> are each electrically connected to a processing unit <b>40</b> which utilizes passively listening and beam forming techniques to measure the process fluid sound speed within hydraulic hose <b>33</b> even though the acoustic pressure sensors are not mounted on the hose. Processing unit <b>40</b> is further configured to determine a gas void fraction of the hydraulic fluid representative of the entrained air content. It should be appreciated by those skilled in the art that, given the current disclosure, that the two sensor array comprised of first acoustic pressure sensor <b>38</b> and second acoustic pressure sensor <b>39</b> are positioned close to changes in the characteristic volumetric impedance of the piping network wherein those changes produce significant acoustic reflections.

For acoustics propagating within ducts for which the mean fluid properties are essentially constant, the characteristic volumetric impedance is a function of the cross sectional area of the duct. As disclosed above, changes in the characteristic volumetric impedance result in reflections of propagating acoustics wave within a duct. Reflections of incident acoustic waves occur for incident acoustic waves from either direction within a piping network. It should therefore be appreciated by those skilled in the art that for a piping network with one or more regions for which acoustics reflections are generated, the resulting acoustic field can be significantly different from the acoustic field that would have been present without any reflections.

Referring next to FIG. <b>9</b>, there is shown a schematic of piping network <b>45</b> including fluid monitoring system <b>51</b>. Piping network <b>45</b> is comprised of an inlet pipe <b>46</b> coupled to a flexible hydraulic hose <b>48</b> by inlet coupling <b>47</b> and outlet pipe <b>50</b> coupled to the flexible hose by outlet coupling <b>49</b>. Fluid monitoring system <b>51</b> comprises a first acoustic pressure sensor <b>52</b>, a second acoustic pressure sensor <b>54</b> and a processing unit <b>53</b>. First acoustic pressure sensor <b>52</b> is electrically coupled to processing unit <b>53</b> by wire <b>55</b> and second acoustic pressure sensor <b>54</b> is electrically coupled to processing unit <b>53</b> by wire <b>56</b>. First acoustic pressure sensor <b>52</b> is positioned within a portion of outlet coupling <b>49</b> and is configured to be acoustically coupled to hydraulic oil within the coupling. Second acoustic pressure sensor <b>52</b> is positioned within a portion of inlet coupling <b>47</b> and is configured to be acoustically coupled to hydraulic oil within the coupling. The pressure transducers are each connected to processing unit <b>53</b> which utilizes passively listening and beam forming techniques disclosed herein above to measure the process fluid (hydraulic oil in this example) sound speed within hydraulic hose <b>48</b> even though the acoustic pressure sensors are not mounted on the hose. Processing unit <b>53</b> is further configured to determine a gas void fraction of the hydraulic fluid. It should be appreciated by those skilled in the art that the two sensor array comprised of first acoustic pressure sensor <b>52</b> and second acoustic pressure sensor <b>54</b> comprise an instrumented section of hydraulic hose that can have a male and a female quick disconnect fitting on either end of the hose. Such an instrumented section of hydraulic hose can have great utility in monitoring and diagnosing problems in a hydraulic system. As part of the present disclosure, first acoustic pressure sensor <b>52</b> and second acoustic pressure sensor <b>54</b> are positioned within, or in close proximity to, couplings <b>49</b> and <b>47</b> respectively and are installed in fluid communication with the process fluid (hydraulic oil) within the section of hydraulic hose <b>48</b> wherein physical changes disclosed herein above produce significant acoustic reflections. The pressure transducers, acoustic pressure sensors <b>52</b>, <b>54</b>, are each connected to processing unit <b>53</b> by respective wires <b>55</b>, <b>56</b> wherein the processing unit utilizes passively listening and beam forming techniques disclosed herein above to measure the process fluid sound speed within the hydraulic hose <b>48</b>. Processing unit <b>53</b> is further configured to determine a gas void fraction of the hydraulic fluid within hydraulic hose <b>48</b> as well as other parameters related to the hydraulic fluid including water entrainment and contaminants.

It should be noted that the instrumented hydraulic system is comprised of hydraulic hose <b>48</b>, inlet coupling portion <b>47</b> including acoustic pressure sensor <b>54</b> and outlet coupling portion <b>49</b> including acoustic pressure sensor <b>52</b> pipe can be inserted anywhere within a hydraulic system where there is a quick disconnect fitting of the same type. For example, if there is a quick disconnect at the inlet of a hydraulic pump (<b>32</b> in FIG. <b>8</b>), the quick disconnect could be disconnected, and the instrumented section of hydraulic hose could be inserted to measure the process fluid speed and interpret a gas void fraction within the piping network that includes the hydraulic pump. It should be further noted that this particular implementation has additional advantages over prior art in that a flexible hydraulic hose effectively minimizes any coherence of structural disturbances across the aperture that could be present on a more rigid conduit. Additionally, for systems in which the length to diameter ratio of the conduit separating the two sensors is large (>10 as disclosed herein above and below), there will be little coherence of vortical disturbances to confound the two sensor beamforming of the present disclosure.

It should be appreciated by those skilled in the art that utilizing an array with an aperture that contains acoustic reflections produced by connectors (as well as other changes in characteristic volumetric impedance) can pose a significant challenge to determining the process fluid sound speed by interpreting the output of the array of acoustic sensors for several reasons.

Firstly, as disclosed herein above, and ideally, a conduit, or piping network within the array would have a constant characteristic volumetric impedance and constant elasticity of the conduit, such that any acoustics reflections within the array would be minimized. Beam forming techniques are best suited for determining the propagation characteristics of a propagating wave when waves propagate in both directions within the aperture unimpeded.

Secondly, the acoustic aperture of a one dimensional array is the length of the array along the direction of sound propagation between the two acoustic pressure sensors. Typically, the longer the aperture, the better the system is able to utilize the typically higher amplitude, lower frequency, long wave length naturally occurring sound within the piping network determine the process fluid sound speed.

Therefore, for many hydraulic networks, the flexible hydraulic hoses offer the best opportunity for unimpeded sound propagation over a long aperture and techniques of the prior art would dictate positioning sensors on the conduit within which the speed of sound sought, i.e. in this case on the comparatively long section of hydraulic hose which comprises the majority of the aperture of the array. It is, however, difficult the install acoustic pressure sensors on a hydraulic hose. Typically, pressure transducers require some type of rigid conduit connector for installation. Rigid conduit connectors often contain cross sectional area changes that produce acoustic reflections, due to area changes and pressure changes and gas void fraction changes as discussed above. These acoustic reflections, if they occur within the aperture of an array of pressure sensors attempting to determine the speed of sound of a process fluid within a conduit, will in general serve to confound the array processing as disclosed herein above.

Referring next to FIG. <b>10</b>, there is shown a cross sectional rendering of a sensor manifold <b>60</b>. Sensor manifold <b>60</b> is comprised of manifold block <b>61</b> including a conduit <b>62</b> running therethrough and slightly beyond the block with male pipe threads positioned on the outer surface. Manifold block <b>61</b> further includes a female thread extending from an outer surface and into conduit <b>62</b> within which acoustic pressure sensor <b>63</b> is threadably engaged and is configured to position the acoustic pressure sensor in fluid communication with a hydraulic fluid with the conduit <b>62</b>. Acoustic pressure sensor <b>63</b> can comprise any pressure sensor configured to sense acoustic waves propagating in the hydraulic fluid and in some implementations can comprise a piezo electric crystal pressure transducer. Manifold block <b>61</b> also includes a first coupling section <b>64</b> threadably engaged onto a first threaded end of conduit <b>62</b> and a second coupling section <b>65</b> threadably engaged onto a second threaded end of conduit <b>62</b>. In this particular implementation, first coupling section <b>64</b> comprising a male quick disconnect coupling section portion and second coupling section <b>65</b> comprises a female quick disconnect coupling section. It should be noted that although the manifold block <b>60</b> could be implemented with any type of connector, it would also benefit from quick disconnects <b>64</b>, <b>65</b>. Manifold block <b>60</b> is particularly useful for applications in which two components are connected with a hydraulic hose that has quick disconnects on both ends. For example, a hose with two male disconnects. This implementation teaches to construct two short conduits sections, each with a male and a female disconnect and a pressure transducer installed on each of the two short conduits. Conduit <b>62</b> of manifold block <b>60</b> can be inserted in between a first hydraulic component, say reservoir <b>31</b> (FIG. <b>8</b>) and the one end of hydraulic hose <b>33</b>, and a second hydraulic component, say pump <b>32</b>, and the other end of the hydraulic hose. As disclosed, inserting a pair of manifold blocks <b>60</b> with acoustic pressure sensors <b>63</b> provides a means to instrument the process fluid within the hydraulic line to provide a process fluid sound speed measurement and from that determine entrained air levels and other parameters of the fluid.

Another embodiment of fittings or manifolds of the current disclosure includes utilizing bleed rings to provide pressure ports into a hydraulic system. Bleed rings can be inserted between two flanges and captured between the two flanges with gaskets on either side. Such an embodiment includes a bleed ring with an ⅛″ NPT acoustic pressure transducer captured between a pair of 1 inch. 150 lb. flanges.

Referring to FIG. <b>11</b>, there is shown an implementation of a fluid monitoring system <b>110</b> in accordance with the current disclosure. Similar to the implementations disclosed herein above with specific reference to FIG. <b>9</b>, fluid monitoring system <b>110</b> is comprised 2 flexible hose sections <b>111</b>, <b>112</b> coupled together by 3 couplings <b>113</b>, <b>114</b>, <b>115</b> each having an acoustic pressure sensor for P<sub>2</sub>, P<sub>3 </sub>and P<sub>4 </sub>acoustic pressure sensors and inlet pipe <b>116</b> having P<sub>1</sub>, positioned therein. The two flexible hose sections <b>111</b>, <b>112</b> can comprise a flexible hydraulic hose. The P<sub>1</sub>, P<sub>2</sub>, P<sub>3 </sub>and P<sub>4 </sub>sensors are electrically connected to a processor configured to output a speed of sound for a fluid flowing in the plurality of flexible hoses <b>111</b>, <b>112</b> using techniques disclosed herein above. It should be appreciated by those skilled in the art that each of the pairs of acoustic pressure sensors form an acoustic aperture of an array and that the various acoustic pressure sensors comprise a number of arrays and can further comprise an array having P<sub>1 </sub>through P<sub>4 </sub>sensors with the acoustic aperture length equaling the length between P<sub>1 </sub>sensor and P<sub>4 </sub>sensor.

It should be appreciated by those skilled in the art that the 4 pressure sensors P<sub>1 </sub>through P<sub>4 </sub>comprise an acoustic array, in which any subset of the 4 pressure transducers containing 2 or more of the 4 pressure transducers also constitute acoustic arrays.

A test was conducted to evaluate ability of the system shown schematically in FIG. <b>11</b> to measure the gas void fraction of bubbly liquids. In operation, water was run through the gas void fraction monitoring system <b>110</b> at a pressure of approximately 45 psig at a rate of about 1.8 kg/sec with varying rates of gas void fractions of air from 0-5%. Referring next to FIG. <b>12</b>, there is shown a graphical representation of the normalized beam forming power versus the speed of sound for water with a gas volume fraction of about 1% as determined by fluid monitoring system <b>110</b> for two acoustic arrays, one array containing pressure sensors P<b>1</b> and P<b>4</b>, denoted as array <b>14</b> line <b>125</b>, and the other array containing pressure sensors P<b>2</b>, P<b>3</b>, and P<b>4</b>, denoted as array <b>234</b> line <b>126</b>. As shown, the normalized beam forming power plot versus sound speed indicated the sound speed with the maximum power occurs at a sound speed of 490 ft/sec for each of the array configurations evaluated. Also as shown, the normalized beam forming power plot versus sound speed from array <b>234</b> exhibits a more pronounced than that associated with array <b>14</b>.

Similarly, and with reference now to FIG. <b>13</b>, there is shown a graphical representation of the normalized beam forming power versus the speed of sound for water with a gas volume fraction of about 2.5% as determined by fluid monitoring system <b>110</b> for the same two acoustic arrays for which the normalized beam forming power is displayed in FIG. <b>12</b>

As shown, the normalized beam forming power plot versus sound speed indicated the sound speed with the maximum power occurs at a sound speed of 350 ft/sec for each of the array configurations evaluated. Also as shown, the normalized beam forming power plot versus sound speed from array <b>234</b> exhibits a more pronounced than that associated with array <b>14</b>.

It should be appreciated by those skilled in the art specific position acoustic pressure used in the beam forming analysis were selected as representative of positions to illustrate the utility of the invention and could be vary without departing from the current disclosure.

Now with reference to FIG. <b>14</b>, there is shown a graphical representation of the measured sound speed versus the reference gas volume fraction as determined by fluid monitoring system <b>110</b> and the normalized beam forming power techniques of FIGS. <b>12</b> and <b>13</b>. Referring now to FIG. <b>15</b>, there is shown a graphical representation of the gas void fraction as determined by fluid monitoring system <b>110</b> versus a reference gas void fraction plotted against a linear fit line. It can be seen that fluid monitoring system <b>110</b> provides a determination of the gas void fraction for a bubbly fluid flowing through a flexible hose that is highly correlated and linear with respect to the reference injected gas volume fraction. The reference injected gas void fraction was determined utilizing measurements of the single phase air and water rates upstream of the injection point and upstream of the test section. Note that some level of departure between any measured gas void fraction and the reference gas volume fraction is expected due to a several sources of uncertainty including the some amount of the injected air dissolving into the undersaturated water, slippage between the air and water phases causing some level of either gas or liquid hold up, uncertainty in the polytropic exponent of the sound propagation within the bubbly mixtures, and the use of estimates of the average pressure within the test section when the actual pressure within the test section decreases due to pressure low due to flow.

Referring to FIG. <b>16</b>, there is shown another implementation of a the a gas void fraction monitoring system <b>160</b> in accordance with the current disclosure. Similar to the implementations disclosed herein above, fluid monitoring system <b>160</b> is comprised a plurality of N flexible hose sections coupled together by N+1 couplings each having an acoustic pressure sensor for P<sub>1</sub>-P<sub>N+1 </sub>sensors. The N flexible hose sections can comprise a flexible hydraulic hose. The P<sub>1</sub>-P<sub>N+1 </sub>sensors are electrically connected to a processor configured to output a speed of sound for a fluid flowing in the plurality of flexible hoses using techniques disclosed herein above. Also shown is a processor for determining the gas void fraction of the fluid using Wood's equation and a static pressure signal of the static pressure of the fluid in the plurality of flexible hoses. It should be appreciated by those skilled in the art that each of the pairs of acoustic pressure sensors form an aperture of an array and that the various acoustic pressure sensors comprise a number of arrays and can further comprise an array having P<sub>N+1 </sub>sensors with the acoustic aperture length equaling the length between P<sub>1 </sub>sensor and P<sub>N+1 </sub>Sensor.

Now with reference to FIGS. <b>17</b>, <b>18</b>, wherein FIG. <b>18</b> comprises the detail of inset <b>18</b> of FIG. <b>17</b>, there is shown another embodiment of fluid monitoring system <b>180</b> in accordance with the present disclosure. Fluid monitoring system <b>180</b> can comprise a gas void fraction monitoring system for continuously or semi-continuously monitoring a gas void fraction of the hydraulic fluid flowing through a hydraulic network. Fluid monitoring system <b>180</b> comprises an array of three acoustic pressure sensors, <b>181</b>, <b>182</b>, <b>183</b>. Acoustic pressure sensors, <b>181</b>, <b>182</b>, <b>183</b> are positioned along the length of hydraulic hose <b>184</b> positioned between a hydraulic reservoir (not shown) and an inlet of a hydraulic pump <b>185</b> on a fluid power test bed. Acoustic pressure sensors, <b>181</b>, <b>182</b>, <b>183</b> are mounted within manifold blocks <b>186</b>, <b>187</b>, <b>188</b> respectively in fluid communication with the hydraulic fluid. Manifold blocks <b>186</b>, <b>187</b>, <b>188</b> are standard JIC fittings that are connected to standard hydraulic hose <b>184</b> with a pressure rating on 4000 psi. Using the coordinate convention disclosed herein above, the first acoustic pressure sensor <b>181</b> is located at location <b>1</b> at X=0, the second acoustic pressure sensor <b>182</b> is positioned at location <b>2</b> at X=28 inches, and the third acoustic pressure sensor <b>183</b> is positioned at location <b>3</b> at X=56 inches. In additional to the three acoustic pressure sensors <b>181</b>, <b>182</b>, <b>183</b>, static pressure sensors <b>189</b>, <b>190</b> are installed at locations <b>1</b> and <b>3</b> in manifold block <b>186</b> and manifold block <b>188</b> respectively. For the purposes of the testing, the static pressures measured at locations <b>1</b> and <b>3</b> were averaged to estimate the pressure of the hydraulic fluid within the array.

Testing was conducted with fluid monitoring system <b>180</b> to evaluate the ability of the system to measure the gas void fraction in the hydraulic fluid flowing in the direction of arrow <b>191</b> within hydraulic hose <b>184</b>. As part of one test, a throttle valve (not shown) was partially closed upstream of location <b>1</b>. The pressure upstream of the restriction was near ambient pressure. As the inlet of the pump <b>185</b> pulled the hydraulic fluid through the restriction introduced by the throttle valve, the pressure in the test section was reduced below ambient, releasing dissolved gases in the hydraulic fluid.

Referring now to FIGS. <b>19</b>, <b>20</b>, there is shown graphical examples of some of the results of the test disclosed herein above. FIG. <b>19</b> shows the normalized beam forming power function as a function of trial sound speed for an array consisting of sensors <b>181</b> and <b>182</b>. At this condition, the average static pressure in the array was measured to be −8.5 psig, (˜6.2 psia) and the sound speed determined from the acoustic aperture comprising the array of sensors <b>181</b> and <b>182</b> was 198 ft/sec at peak <b>200</b>, corresponding to a gas void fraction of 1.3%. As shown, the power function provides a clear and unambiguous indication of the sound speed of the process fluid within the acoustic aperture of the array. The prominence of the peak <b>200</b> at a positive sound speed of 198 ft/sec indicates that most of the noise in propagating in the direction of the flow <b>191</b>.

FIG. <b>20</b> shows the power function at the same operation set point of the hydraulic test bed, but for an array consisting of acoustic pressure sensors, <b>181</b>, <b>182</b>, <b>183</b>. For this array, the measured sound speed at this same nominal set point is 173 ft/sec at peak <b>210</b> in the direction of flow <b>191</b>, corresponding to a gas void fraction of 1.7%. The power function for the 3 sensor array indicates a sound field in which the sound field is more balanced, with sound propagating with comparable intensity both in the direction of flow <b>191</b> associated with peak <b>210</b> and against the direction of the flow associated with peak <b>211</b>. This difference may likely be due to the proximity of the pump <b>185</b> to the end of the three sensor array with the pump generating noise that propagates within the hydraulic hose <b>184</b> entering through manifold block <b>188</b>.

Differences between the sound speed measured from the two arrays at the same operating conditions can, at least in part, be attributed to the gas void fraction changing within the array due to pressure losses due to friction. The static pressure in the array is highest at sensor <b>189</b>, and decreases through the array, toward the inlet of the pump. It should also be appreciated that the static pressure utilized to determine the gas void fraction using Wood's Equation is based on the measured sound speed from each configuration and was assumed to be the same, although in reality, the average static pressure within the array consisting of acoustic pressure sensors <b>181</b> and <b>182</b> is higher than the average pressure in the array consisting of acoustic pressure sensors <b>181</b>, <b>182</b> and <b>183</b> due to the static pressure loss described above. The description of the test above and the data presented provides an example of the utility and flexibility of the fluid monitoring system of this disclosure.

The foregoing disclosure provides illustration and description but is not intended to be exhaustive or to limit the implementations to the precise form disclosed. Modifications may be made in light of the above disclosure or may be acquired from practice of the implementations. As used herein, the term “component” is intended to be broadly construed as hardware, firmware, or a combination of hardware and software. It will be apparent that systems and/or methods described herein may be implemented in different forms of hardware, firmware, and/or a combination of hardware and software. The actual specialized control hardware or software code used to implement these systems and/or methods is not limiting of the implementations. Thus, the operation and behavior of the systems and/or methods are described herein without reference to specific software code—it being understood that software and hardware can be used to implement the systems and/or methods based on the description herein. As used herein, satisfying a threshold may, depending on the context, refer to a value being greater than the threshold, greater than or equal to the threshold, less than the threshold, less than or equal to the threshold, equal to the threshold, and/or the like, depending on the context. As used herein, the terms acoustic pressure sensor, acoustic transducer and transducer are used to mean the same element and include a device configured to measure the unsteady pressure of a fluid are different and distinguished form devices configured to measure steady (or DC) pressures a fluid. Although particular combinations of features are recited in the claims and/or disclosed in the specification, these combinations are not intended to limit the disclosure of various implementations. In fact, many of these features may be combined in ways not specifically recited in the claims and/or disclosed in the specification.

Although each dependent claim listed below may directly depend on only one claim, the disclosure of various implementations includes each dependent claim in combination with every other claim in the claim set. No element, act, or instruction used herein should be construed as critical or essential unless explicitly described as such. Also, as used herein, the articles “a” and “an” are intended to include one or more items and may be used interchangeably with “one or more.” Further, as used herein, the article “the” is intended to include one or more items referenced in connection with the article “the” and may be used interchangeably with “the one or more.” Furthermore, as used herein, the term “set” is intended to include one or more items (e.g., related items, unrelated items, a combination of related and unrelated items, and/or the like), and may be used interchangeably with “one or more.” Where only one item is intended, the phrase “only one” or similar language is used. Also, as used herein, the terms “has,” “have,” “having,” or the like are intended to be open-ended terms. Further, the phrase “based on” is intended to mean “based, at least in part, on” unless explicitly stated otherwise. Also, as used herein, the term “or” is intended to be inclusive when used in a series and may be used interchangeably with “and/or,” unless explicitly stated otherwise (e.g., if used in combination with “either” or “only one of”).

## Claims

1. A fluid measuring system comprising:
a piping network comprising;
a flexible hydraulic hose comprising:
a hose length;
a hose diameter
a first end portion and a second end portion; and

a first fitting coupled to the first end portion and a second fitting coupled to the second end portion;
an acoustic array comprising:
a first acoustic pressure sensor positioned proximate the first fitting;
a second acoustic pressure sensor positioned proximate the second fitting; and
an acoustic aperture that spans an aperture length between the first acoustic pressure sensor and the second acoustic pressure sensor; and


a processing unit that determines a speed of sound of a process fluid within the piping network and within acoustic aperture using the first acoustic pressure sensor and the second acoustic pressure sensor.

2. The fluid measuring system of claim 1 wherein the first acoustic pressure sensor and the second acoustic pressure sensor are not positioned on the flexible hydraulic hose.

3. The fluid measuring system of claim 1 wherein the first fitting and the second fitting produce at least one change in a characteristic volumetric impedance within the acoustic aperture wherein the at least one change in a characteristic volumetric impedance is at least 25%.

4. The fluid measuring system of claim 3 wherein the first fitting and the second fitting produce at least one change in a characteristic volumetric impedance within the acoustic aperture.

5. The fluid measuring system of claim 4 further comprising:
a plurality of reflections of incident acoustic waves produced by the at least one change in a characteristic volumetric impedance in the process fluid within the aperture; and
the processing unit is configured to determine the speed of sound of the process fluid within the acoustic aperture in the presence of the plurality of reflections of incident acoustic waves.

6. The fluid measuring system of claim 1 wherein at least one of the first fitting and the second fitting comprise at least a portion of a quick disconnect fitting.

7. The fluid measuring system of claim 6 wherein the first fitting comprises at least a portion of a first quick disconnect fitting and the second fitting comprises at least a portion of a second quick disconnect fitting.

8. The fluid measuring system of claim 7 wherein the first acoustic pressure sensor is positioned in the first quick disconnect fitting and the second acoustic pressure sensor is positioned in the second quick disconnect fitting.

9. The fluid measuring system of claim 1 further comprising at least one manifold block coupled to any of the first fitting and the second fitting and wherein any of the first acoustic pressure sensor and the second acoustic pressure sensor is positioned in the at least one manifold block.

10. The fluid measuring system of claim 1 wherein the first acoustic pressure sensor and the second acoustic pressure sensor are configured to be in fluid communication with the process fluid.

11. The fluid measuring system of claim 10 wherein the first acoustic pressure sensor and the second acoustic pressure sensor comprise piezo electric crystal pressure transducers.

12. The fluid measuring system of claim 1 wherein the piping network further comprises any of a reservoir, a pump, an actuator, a manifold, and a filter and wherein at least one of the first fitting and the second fitting is coupled to any of the reservoir, the pump, the actuator, the manifold, and the filter.

13. The fluid measuring system of claim 1 further comprising the processing unit configured to determine an entrained air content of the process fluid using the speed of sound.

14. The fluid measuring system of claim 1 further comprising the processing unit configured to determine a physical property of the process fluid using the speed of sound.

15. The fluid measuring system of claim 1 further comprising the processing unit configured to determine changes in the process fluid using the speed of sound.

16. The fluid measuring system of claim 1 further comprising the processing unit configured to determine a presence of at least one contaminate in the process fluid using the speed of sound.

17. The fluid measuring system of claim 1 further comprising the processing unit configured to determine a diagnostic state of the piping network using the speed of sound.

18. The fluid measuring system of claim 1 wherein the hose length is substantially equal to the acoustic aperture.

19. The fluid measuring system of claim 1 wherein the flexible hydraulic hose is comprised of an elastomer material.

20. The fluid measuring system of claim 19 wherein the flexible hydraulic hose is comprised of a composite having a plurality of materials and wherein the plurality of materials include at least one elastomer material and at least one reinforcing material.

21. The fluid measuring system of claim 1 wherein the flexible hydraulic hose is comprised of an elastomer material having an elastic modulus of less than 1,000,000 psi and an elongation at yield of greater than 5%.

22. The fluid measuring system of claim 1 wherein the aperture length is greater than ten times the hose diameter.

23. The fluid measuring system of claim 1 wherein the piping network includes coherent acoustic waves, coherent vortical structures, and coherent propagating structural disturbances; and
wherein the piping network is configured to preferentially reduce the coherence between the signals measured by the first acoustic pressure sensor and the second acoustic pressure sensor associated with the coherent vortical structures, and coherent propagating structural disturbances.

24. A fluid measuring method comprising:
providing a piping network comprising;
a flexible hydraulic hose comprising:
a hose length;
a hose diameter
a first end portion and a second end portion; and

a first fitting coupled to the first end portion and a second fitting coupled to the second end portion;
an acoustic array comprising:
a first acoustic pressure sensor positioned proximate the first fitting;
a second acoustic pressure sensor positioned proximate the second fitting; and
an acoustic aperture that spans an aperture length between the first acoustic pressure sensor and the second acoustic pressure sensor;


providing a processing unit; and
determining, with the processing unit, a speed of sound of a process fluid within the piping network and within acoustic aperture using the first acoustic pressure sensor and the second acoustic pressure sensor.

25. The fluid measuring method of claim 24 further comprising positioning the first acoustic pressure sensor and the second acoustic pressure sensor beyond the first end portion and the second end portion of the flexible hydraulic hose.

26. The fluid measuring method of claim 24 further comprising producing at least one change in a characteristic volumetric impedance within the acoustic aperture wherein the at least one change in a characteristic volumetric impedance is at least 25%.

27. The fluid measuring method of claim 26 further comprising producing at least one change in a characteristic volumetric impedance within the acoustic aperture.

28. The fluid measuring method of claim 27 further comprising:
producing a plurality of reflections of incident acoustic waves using the at least one change in a characteristic volumetric impedance in the process fluid within the aperture; and
determining with the processing unit the speed of sound of the process fluid within the acoustic aperture in the presence of the plurality of reflections of incident acoustic waves.

29. The fluid measuring method of claim 24 wherein at least one of the first fitting and the second fitting comprise at least a portion of a quick disconnect fitting.

30. The fluid measuring method of claim 29 wherein the first fitting comprises at least a portion of a first quick disconnect fitting and the second fitting comprises at least a portion of a second quick disconnect fitting.

31. The fluid measuring method of claim 30 further comprising positioning the first acoustic pressure sensor in the first quick disconnect fitting and positioning the second acoustic pressure sensor in the second quick disconnect fitting.

32. The fluid measuring method of claim 24 further comprising coupling at least one manifold block to any of the first fitting and the second fitting and positioning any of the first acoustic pressure sensor and the second acoustic pressure sensor in the at least one manifold block.

33. The fluid measuring method of claim 24 further comprising positioning the first acoustic pressure sensor and the second acoustic pressure sensor in fluid communication with the process fluid.

34. The fluid measuring method of claim 33 wherein the first acoustic pressure sensor and the second acoustic pressure sensor comprise piezo electric crystal pressure transducers.

35. The fluid measuring method of claim 24 wherein the piping network further comprises any of a reservoir, a pump, an actuator, a manifold, and a filter, the method further comprising coupling at least one of the first fitting and the second fitting to any of the reservoir, the pump, the actuator, the manifold, and the filter.

36. The fluid measuring method of claim 24 further comprising determining, with the processing, an entrained air content of the process fluid using the speed of sound.

37. The fluid measuring method of claim 24 further comprising determining, with the processing unit, a physical property of the process fluid using the speed of sound.

38. The fluid measuring method of claim 24 further comprising the processing unit configured to determine changes in the process fluid using the speed of sound.

39. The fluid measuring method of claim 24 further comprising determining, with the processing unit, a presence of at least one contaminate in the process fluid using the speed of sound.

40. The fluid measuring method of claim 24 further comprising determining, with the processing unit, a diagnostic state of the piping network using the speed of sound.

41. The fluid measuring method of claim 24 wherein the hose length is substantially equal to the acoustic aperture.

42. The fluid measuring method of claim 24 wherein the flexible hydraulic hose is comprised of an elastomer material.

43. The fluid measuring method of claim 42 wherein the flexible hydraulic hose is comprised of a composite having a plurality of materials and wherein the plurality of materials include at least one elastomer material and at least one reinforcing material.

44. The fluid measuring method of claim 24 wherein the flexible hydraulic hose is comprised of an elastomer material having an elastic modulus of less than 1,000,000 psi and an elongation at yield of greater than 5%.

45. The fluid measuring method of claim 24 wherein the aperture length is greater than ten times the hose diameter.

46. The fluid measuring method of claim 24 wherein the piping network includes coherent acoustic waves, coherent vortical structures, and coherent propagating structural disturbances; and
the method further comprises reducing the coherence between the signals measured by the first acoustic pressure sensor and the second acoustic pressure sensor associated with the coherent vortical structures, and coherent propagating structural disturbances.

