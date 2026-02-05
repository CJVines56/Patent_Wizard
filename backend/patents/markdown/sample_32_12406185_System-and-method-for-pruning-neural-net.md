# System and method for pruning neural networks at initialization using iteratively conserving synaptic flow (Doc 12406185)

- Doc ID: 12406185
- Title: System and method for pruning neural networks at initialization using iteratively conserving synaptic flow
- Filing Date: 20210715
- Classification: G06N 3/082
- Authors: Hidenori Tanaka; Daniel Kunin; Daniel L. K. Yamins; Surya Ganguli

## Abstract

A system and method to prune parameters of a neural network at initialization uses iterative conserving synaptic flow that saves time, memory and energy both during training and at test time of the neural network. The result of the disclosed pruning system and method are highly sparse trainable subnetworks at initialization, without training and without ever looking at the data (a data agnostic pruning system and method). The pruning system and method preserves the total flow of synaptic strengths through the network at initialization subject to a sparsity constraint.

## Description

This application claims the benefit under 35 USC 119(e) to U.S. Provisional Patent Application Ser. No. 63/052,317 filed Jul. 15, 2020 that is incorporated herein by reference.

Appendix A (3 pages) has further proofs, hyperparameter choices for the SynFlow method and further experimental details that are incorporated herein and form part of the specification.

The disclosure relates generally to neural network parameter pruning and in particular to a system and method for implementing an data agnostic iteratively conserving synaptic flow pruning system and method for neural networks parameters.

Network pruning, or the compression of neural networks by removing parameters, has been an important subject both for reasons of practical deployment as discussed in [1], [2], [3], [4], [5], [6], [7] and for theoretical understanding of artificial [8] and biological [9] neural networks. Conventionally, pruning algorithms have focused on compressing pre-trained models [1], [2], [3], [5], [6].

However, recent works [10], [11] have identified through iterative training and pruning cycles using iterative magnitude pruning that there exist sparse subnetworks (known as “winning tickets”) in randomly-initialized neural networks that, when trained in isolation, can match the test accuracy of the original network. Moreover, it has been shown that some of these winning ticket subnetworks can generalize across datasets and optimizers [12]. While these results suggest training can be made more efficient by identifying winning ticket subnetworks at initialization, they do not provide any efficient algorithms to find them. Typically, it requires significantly more computational costs to identify winning tickets through iterative training and pruning cycles than simply training the original network from scratch [10], [11].

It is known that a neural network can be compressed in different ways including using micro-architectures [15], [16], [17], dimensionality reduction of network parameters [18], [19], and training of dynamic sparse networks [20], [21]. A preferred method involves neural network pruning.

Neural Network Pruning

Neural network pruning may be done after training or before training. When the pruning is performed after training, conventional pruning algorithms assign scores to parameters in neural networks after training and remove the parameters with the lowest scores [5], [22], [23]. Popular scoring metrics include weight magnitudes [4], [6], its generalization to multi-layers [24], first- [25], [26], [27] and second-order [2], [3], [27] Taylor coefficients of the training loss with respect to the parameters, and more sophisticated variants [28], [29], [30]. While these pruning algorithms can indeed compress neural networks at test time, there is no reduction in the cost of training which can be very expensive.

Recent works demonstrated that randomly initialized neural networks can be pruned before training with little or no loss in the final test accuracy [43], [32], [31]. In particular, the Iterative Magnitude Pruning (IMP) algorithm [10], [11] repeats multiple cycles of training, pruning, and weight rewinding to identify extremely sparse neural networks at initialization that can be trained to match the test accuracy of the original network. While IMP is powerful, it requires multiple cycles of expensive training and pruning with very specific sets of hyperparameters.

Avoiding these difficulties, a different approach uses the gradients of the training loss at initialization to prune the network in a single-shot [13], [14]. While these single-shot pruning algorithms at initialization are much more efficient, and work as well as IMP at moderate levels of sparsity, they suffer from layer-collapse, or the premature pruning of an entire layer rendering a network untrainable [13], [33]. Thus, these known methods suffer from layer collapse as shown in FIG. <b>8</b> in which each of the known methods (random, magnitude, SNIP, GraSP has their Top-1 accuracy reduces to zero before the maximum compression is reached.

Layer Collapse in Neural Network Pruning at Initialization

Thus, a key obstacle to pruning at initialization is layer collapse. Layer-collapse occurs when an algorithm prunes all parameters in a single weight layer even when prunable parameters remain elsewhere in the network. This renders the network untrainable, evident by sudden drops in the achievable accuracy for the network as shown in FIG. <b>8</b> as discussed above.

Broadly speaking, a pruning algorithm at initialization is defined by two steps in which a first step scores the parameters of a network according to some metric and the second step masks the parameters (removes or keeps the parameter) according to their scores. As discussed above, layer collapse leads to a sudden drop in accuracy. Thus, existing neural network parameter pruning methods all have the key problem of layer collapse [32], [14], [33/42] for existing neural network pruning algorithms using global-masking.

It is desirable to provide neural network pruning at initialization system and method that solves the above technical problem of layer collapse and computationally expensive pruning and can provide a highly sparse trainable subnetworks technical solution and maximum compression while being able to do so at initialization and without training data so that the system and method are data agnostic and it is to this end that the disclosure is directed.

FIG. <b>1</b> illustrates an example of a neural network having one or more layers;

FIGS. <b>2</b>A and <b>2</b>B show an example of a neural network at initialization and after typical parameter pruning;

FIGS. <b>3</b>A and <b>3</b>B illustrate a compression ratio and an average square magnitude score per layer for a known magnitude pruning process;

FIG. <b>4</b> illustrates a example of a computing device that may generate a highly sparse trainable subnetworks at initialization using a novel SynFlow process and utilize the highly sparse trainable subnetworks;

FIG. <b>5</b> illustrates more details of an implementation of the SynFlow system;

FIG. <b>6</b> illustrates an iterative snaptic flow pruning method;

FIG. <b>7</b> is an example of the pseudcode for the iterative snaptic flow pruning method;

FIG. <b>8</b> shows a compression ratio of various known pruning processes as compared to the SynFlow method;

FIG. <b>9</b> shows a layer collapse of various known pruning processes as compared to layer collapse of the SynFlow method;

FIG. <b>10</b>A shows a neuron-wise conservation of score for various known pruning processes as compared to layer collapse of the SynFlow method;

FIG. <b>10</b>B shows an inverse relationship between layer size and average layer score of various known pruning processes as compared to layer collapse of the SynFlow method; and

FIG. <b>11</b> illustrates top-1 test accuracy as a function of different compression ratios for known pruning methods and the SynFlow method over twelve different models and datasets.

The disclosure is particularly applicable to the SynFlow process described below and it is in this context that the disclosure will be described. It will be appreciated, however, that the system and method has greater utility since the it may be varied that is within the scope of the disclosure.

The system and method may generate, an initialization a highly sparse trainable subnetwork that is data agnostic and may use, in one embodiment, an iterative synaptic flow pruning process to generate the highly sparse trainable subnetwork that achieves maximum compression of the neural network while avoiding layer collapse. The system and method may be implemented using other methods that achieve the highly sparse trainable subnetwork with maximum compression and no layer collapse that are within the scope of this disclosure.

FIG. <b>1</b> illustrates an example of a neural network <b>100</b> having one or more layers. In the example in FIG. <b>1</b>, the neural network has an input layer, one or more hidden layers (such as hidden layer <b>1</b> and hidden layer <b>2</b> as shown in FIG. <b>1</b>) and an output layer. Each layer, such as the input layer or hidden layer <b>1</b>, has one or more neurons <b>102</b> (each with one or more parameters) that make up each layer. The connections between the neurons may be assigned a weight as is well known in the art. As is known in the art, a neural network may have a plurality of layers each with a plurality of neurons so that it is desirable to be able to prune the neurons in the neural network as described above to reduce the time and computation resources required by the neural network in training or in use.

FIGS. <b>2</b>A and <b>2</b>B show an example of a neural network <b>100</b> at initialization and the neural network <b>100</b> after typical parameter pruning in which neurons at certain layers (pruning neurons) and certain connections between neurons (pruning synapses) are eliminated as is known in the art. In some pruning methods, the method always mask the parameters by simply removing the parameters with the smallest scores. This ranking process can be applied globally across the network, or layer-wise and empirically, it has been shown that global-masking performs far better than layer-masking, in part because it introduces fewer hyperparameters and allows for flexible pruning rates across the network [23].

Layer Collapse

As discussed above, one problem for typical neural network pruning methods is the phenomenon known as layer collapse that does not occur in the novel pruning method disclosed below as shown in FIG. <b>8</b> and discussed in more detail below. To gain insight into the phenomenon of layer-collapse, it is useful to define some useful terms inspired by a recent paper studying this failure mode [30].

Given a network, a compression ratio (p) is the number of parameters in the original network divided by the number of parameters remaining after pruning. For example, when the compression ratio ρ=10<sup>3</sup>, then only one out of a thousand of the parameters remain after pruning. A Max compression (ρ<sub>max</sub>) is the maximal possible compression ratio for a network that doesn't lead to layer-collapse. For example, for a network with L layers and N parameters, ρ<sub>max</sub>=N/L, which is the compression ratio associated with pruning all but one parameter per layer. A Critical compression (ρ<sub>CR</sub>) is the maximal compression ratio a given pruning method can achieve without inducing layer-collapse. In particular, the critical compression of a pruning method is always upper bounded by the max compression of the network: ρ<sub>CR</sub>≤ρ<sub>max</sub>. This inequality motivates the following new axiom that any successful pruning method should satisfy.

Axiom. Maximal Critical Compression—The critical compression of a pruning algorithm applied to a network should always equal the max compression of that network. In other words, this axiom implies a pruning algorithm should never prune a set of parameters that results in layer-collapse if there exists another set of the same cardinality that will keep the network trainable. No existing pruning algorithms known with global-masking satisfies this simple axiom which means layer collapse that is a technical problem with these known neural network pruning methods that use global-masking.

Any pruning algorithm could be modified to satisfy the axiom by introducing specialized layer-wise pruning rates. However, to retain the benefits of global-masking [23], the modification of any pruning method would not provide the goal of a pruning method with global-masking that does not cause layer collapse. However, the disclosed SynFlow pruning method satisfies this axiom while maintaining the global-masking in a data agnostic manner and thus provides a technical solution to the technical problem of the known pruning methods and the disclosed SynFlow method and system outperforms existing state-of-the-art pruning algorithms (as shown in FIG. <b>8</b> and discussed below), all while not using the data or requiring training.

To provide evidence of the technical benefit of the novel SynFlow system and method, the SynFlow process is benchmarked against two simple baselines (random scoring and scoring based on weight magnitudes (Magnitude) which are lines farthest to the left and having the lowest compression ratio as shown in FIG. <b>8</b>) as well as two state-of-the-art known single-shot pruning algorithms, Single-shot Network Pruning based on Connection Sensitivity (SNIP) [13] and Gradient Signal Preservation (GraSP) [14] that are also shown in FIG. <b>8</b>. SNIP [13] is a pioneering algorithm to prune neural networks at initialization by scoring weights based on the gradients of the training loss. GraSP [14] is a more recent algorithm that aims to preserve gradient flow at initialization by scoring weights based on the Hessian-gradient product. Both SNIP and GraSP have been thoroughly benchmarked by [14] against other state-of-the-art pruning algorithms that involve training [2], [34], [10], [11], [35], [21], [20], demonstrating competitive performance. As shown in FIG. <b>8</b>, however, all of the existing pruning methods suffer from layer collapse (since none achieves the maximum compression) and has low compression ratios that once again show that each of the existing pruning method has the same technical problem that is solved by the novel SynFlow system and method as described below in more detail.

Conservation Laws of Synaptic Saliency

As shown in FIG. <b>8</b>, with increasing compression ratios, existing random, magnitude, and gradient-based pruning algorithms will prematurely prune an entire layer (layer collapse) making the network untrainable. It is desirable to understand why certain score metrics lead to layer-collapse. FIG. <b>9</b> shows the fraction of parameters remaining at each layer of the same known VGG-19 data model pruned at initialization with ImageNet over a range of compression ratios (4<sup>n </sup>for n=0, 1, . . . , 11). A higher transparency shown in FIG. <b>9</b> represents a higher compression ratio and a dashed line indicates that there is at least one layer with no parameters, implying layer-collapse has occurred for that algorithm. Random pruning (far left chart in FIG. <b>9</b>) prunes every layer in a network by the same amount, evident by the horizontal lines. With random pruning, the smallest layer which is the layer with the least parameters, is the first to be fully pruned.

Conversely, magnitude pruning (second chart in FIG. <b>9</b>) prunes layers at different rates, evident by the staircase pattern in FIG. <b>9</b>. The Magnitude pruning effectively prunes parameters based on the variance of their initialization, which for common network initializations, such as Xavier [36] or Kaiming [37], and are inversely proportional to the width of a layer [33/42]. With magnitude pruning the widest layers which are the layers with largest input or output dimensions, are the first to be fully pruned.

The gradient-based pruning algorithms SNIP [13] and GraSP [14] also prune layers at different rates, but it is less clear about the root cause for this preference. In particular, both SNIP and GraSP aggressively prune the largest layer which is the layer with the most trainable parameters, evident by the sharp peaks in FIG. <b>9</b>.

Based on these observations, gradient-based scores averaged within a layer are inversely proportional to the layer size. To test this, a theoretical framework grounded in flow networks is constructed in which: 1) a general class of gradient-based scores is defined to prove a conservation law for these scores; and 2) use this law to prove that the inverse proportionality between layer size and average layer score holds exactly.

A General Class of Gradient-Based Scores

Synaptic saliency is any score metric that can be expressed as the Hadamard product:

𝒮
   ⁡
   (
   θ
   )
  
  =
  
   
    
     
      ∂
      ℛ
     
     
      ∂
      θ
     
    
    ⊙
    θ
   
   .
  
 


<br/>
where R is a scalar loss function of the output of a feed-forward network parameterized by θ. When R is the training loss L, the resulting synaptic saliency metric is equivalent (modulo sign) to

-
   
    
     
      ∂
      ℒ
     
     
      ∂
      θ
     
    
    ⊙
    θ
   
  
  ,
 


<br/>
the score metric used in Skeletonization [1], one of the first network pruning algorithms. The resulting metric is also closely related to

❘
   "\[LeftBracketingBar]"
  
  
   
    
     ∂
     ℒ
    
    
     ∂
     θ
    
   
   ⊙
   θ
  
  
   ❘
   "\[RightBracketingBar]"
  
 


<br/>
that is the score used in SNIP [13],

-
  
   
    (
    
     H
     ⁢
     
      
       ∂
       ℒ
      
      
       ∂
       θ
      
     
    
    )
   
   ⊙
   θ
  
 


<br/>
the score used in GraSP, and

(
   
    
     
      ∂
       
      ℒ
     
     
      ∂
       
      θ
     
    
    ⊙
    θ
   
   )
  
  2
 


<br/>
the score used in the pruning after training algorithm Taylor-FO [27]. This general class of score metrics, while not encompassing, exposes key properties of gradient-based scores used for pruning.
<br/>
The Conservation of Synaptic Saliency

All synaptic saliency metrics respect two surprising conservation laws that hold at any initialization and step in training.

Theorem 1. Neuron-wise Conservation of Synaptic Saliency—For a feedforward neural network with homogenous activation functions, ϕ=ϕ′(x)x, (e.g. ReLU, Leaky ReLU, linear), the sum of the synaptic saliency for the incoming parameters to a hidden neuron (S<sup>in</sup>) is equal to the sum of the synaptic saliency for the outgoing parameters from the hidden neuron (S<sup>out</sup>).

To prove this theorem 1, consider the j<sup>th </sup>hidden neuron of a network with outgoing parameters θ<sub>ij</sub><sup>out </sup>and incoming parameters θ<sub>jk</sub><sup>in</sup>, such that

∂
    ℛ
   
   
    ∂
    
     ϕ
     ⁡
     (
     
      z
      j
     
     )
    
   
  
  =
  
   
    
     ∑
      
    
    i
   
   ⁢
   
    
     ∂
      
     ℛ
    
    
     ∂
     
      z
      i
     
    
   
   ⁢
   
    θ
    ij
    out
   
  
 


<br/>
and

z
   j
  
  =
  
   
    
     ∑
      
    
    k
   
   ⁢
   
    θ
    jk
    in
   
   ⁢
   
    
     ϕ
     ⁡
     (
     
      z
      k
     
     )
    
    .
   
  
 


<br/>
The sum of the synaptic saliency for the outgoing parameters is:

𝒮
   out
  
  =
  
   
    
     ∑
     i
    
     
    
     
      
       ∂
        
       ℛ
      
      
       ∂
       
        θ
        ij
        out
       
      
     
     ⁢
     
      θ
      ij
      out
     
    
   
   =
   
    
     
      ∑
      i
     
      
     
      
       
        ∂
         
        ℛ
       
       
        ∂
         
        
         z
         i
        
       
      
      ⁢
      
       ϕ
       ⁡
       (
       
        z
        j
       
       )
      
      ⁢
      
       θ
       ij
       out
      
     
    
    =
    
     
      
       (
       
        
         ∑
         i
        
         
        
         
          
           ∂
            
           ℛ
          
          
           ∂
            
           
            z
            i
           
          
         
         ⁢
         
          θ
          ij
          out
         
        
       
       )
      
      ⁢
      
       ϕ
       ⁡
       (
       
        z
        j
       
       )
      
     
     =
     
      
       
        ∂
         
        ℛ
       
       
        ∂
         
        
         ϕ
         ⁡
         (
         
          z
          j
         
         )
        
       
      
      ⁢
      
       ϕ
       ⁡
       (
       
        z
        j
       
       )
      
     
    
   
  
 


<br/>
The sum of the synaptic saliency for the incoming parameters is:

𝒮
   in
  
  =
  
   
    
     ∑
     k
    
     
    
     
      
       ∂
        
       ℛ
      
      
       ∂
       
        θ
        jk
        in
       
      
     
     ⁢
     
      θ
      jk
      in
     
    
   
   =
   
    
     
      ∑
      k
     
      
     
      
       
        ∂
         
        ℛ
       
       
        ∂
         
        
         z
         j
        
       
      
      ⁢
      
       ϕ
       ⁡
       (
       
        z
        k
       
       )
      
      ⁢
      
       θ
       jk
       in
      
     
    
    =
    
     
      
       
        ∂
         
        ℛ
       
       
        ∂
         
        
         z
         j
        
       
      
      ⁢
      
       (
       
        
         ∑
         k
        
         
        
         
          θ
          jk
          in
         
         ⁢
         
          ϕ
          ⁡
          (
          
           z
           k
          
          )
         
        
       
       )
      
     
     =
     
      
       
        ∂
         
        ℛ
       
       
        ∂
         
        
         z
         j
        
       
      
      ⁢
      
       z
       j
      
     
    
   
  
 


<br/>
When φ is homogeneous, then

∂
      
     ℛ
    
    
     ∂
      
     
      ϕ
      ⁡
      (
      
       z
       j
      
      )
     
    
   
   ⁢
   
    ϕ
    ⁡
    (
    
     z
     j
    
    )
   
  
  =
  
   
    
     ∂
      
     ℛ
    
    
     ∂
      
     
      z
      j
     
    
   
   ⁢
   
    
     z
     j
    
    .
   
  
 


<br/>
The neuron-wise conservation of synaptic saliency implies network conservation as well.

Theorem 2. Network-wise Conservation of Synaptic Saliency. —The sum of the synaptic saliency across any set of parameters that exactly separates the input neurons x from the output neurons y of a feedforward neural network with homogenous activation functions equals

〈
   
    
     
      ∂
       
      ℛ
     
     
      ∂
       
      x
     
    
    ,
    
     x
     ^
    
   
   〉
  
  =
  
   
    〈
    
     
      
       ∂
        
       ℛ
      
      
       ∂
        
       y
      
     
     ,
     
      y
      ^
     
    
    〉
   
   .

Theorem 2 is proven in Appendix A by applying the neuron-wise conservation law recursively. Similar conservation properties have been noted in the neural network interpretability literature and have motivated the construction of interpretability methods such as Conductance [38] and Layer-wise Relevance Propagation [39], which have recently been modified for network pruning [9], [40]. While the interpretability literature has focused on attribution to the input pixels and hidden neuron activations, the SynFlow method uses conservation laws that are more general and applicable to any parameter and neuron in a network. Remarkably, these conservation laws of synaptic saliency apply to modern neural network architectures and a wide variety of neural network layers (e.g. dense, convolutional, batchnorm, pooling, residual) as visually demonstrated in FIG. <b>10</b>A in which each dot represents a hidden unit from the feature-extractor of a VGG-19 model pruned at initialization with ImageNet, the location of each dot corresponds to the total score for the unit's incoming and outgoing parameters, (S<sup>in </sup>and S<sup>out</sup>) and the black dotted line represents exact neuron-wise conservation of score.

FIG. <b>10</b>B shows the inverse relationship between layer size and average layer score with each dot represents a layer from a VGG-19 model pruned at initialization with ImageNet, the location of each dot corresponds to the layer's average score and inverse number of elements and the black dotted line represents a perfect linear relationship.

Conservation and Single-Shot Pruning Leads to Layer-Collapse

The conservation laws of synaptic saliency provide the method with the theoretical tools to validate the earlier hypothesis of inverse proportionality between layer size and average layer score as a root cause for layer-collapse of gradient-based pruning methods. Consider the set of parameters in a layer of a simple, fully connected neural network. This set would exactly separate the input neurons from the output neurons. Thus, by the network-wise conservation of synaptic saliency (theorem 2 above), the total score for this set is constant for all layers, implying the average is inversely proportional to the layer size. This relationship can be empirically evaluated at scale for existing pruning methods by computing the total score for each layer of a model, as shown in FIG. <b>10</b>B. While this inverse relationship is exact for synaptic saliency, other closely related gradient-based scores, such as the scores used in SNIP and GraSP, also respect this relationship. This validates the empirical observation that for a given compression ratio, gradient-based pruning methods will disproportionately prune the largest layers. Thus, if the compression ratio is large enough and the pruning score is only evaluated once, then a gradient-based pruning method will completely prune the largest layer leading to layer-collapse.

Magnitude Pruning Avoids Layer-Collapse with Conservation and Iteration

Known iterative pruning methods appear to avoid the layer collapse issue, but cannot generate the highly sparse neural networks. For example, Iterative Magnitude Pruning (IMP or Magnitude as shown in the figures) is a recently proposed pruning algorithm that has proven to be successful in finding extremely sparse trainable neural networks at initialization (winning lottery tickets) [10], [11], [12], [41], [33], [43], [44]. The algorithm follows three simple steps that include: First train a network, second prune parameters with the smallest magnitude, third reset the unpruned parameters to their initialization and repeat until the desired compression ratio. While simple and powerful, IMP is impractical as it involves training the network several times, essentially defeating the purpose of constructing a sparse initialization, but does not suffer from the same catastrophic layer-collapse that other pruning at initialization to which other methods are susceptible.

As has been noted previously [10], [11], iteration is essential for stabilizing IMP. In fact, without sufficient pruning iterations, IMP will suffer from layer-collapse, evident in the sudden accuracy drops for the darker curves in FIG. <b>3</b>B. However, the number of pruning iterations alone cannot explain IMP's success at avoiding layer-collapse. Notice that if MIP didn't train the network during each prune cycle, then, no matter the number of pruning iterations, it would be equivalent to single-shot magnitude pruning with layer collapse. Thus, something very critical must happen to the magnitude of the parameters during training, that when coupled with sufficient pruning iterations allows IMP to avoid layer-collapse. The gradient descent training effectively encourages the scores to observe an approximate layer-wise conservation law, which when coupled with sufficient pruning iterations allows IMP to avoid layer-collapse.

FIGS. <b>3</b>A and <b>3</b>B illustrate a compression ratio and an average square magnitude score per layer for a known magnitude pruning process. As shown in FIG. <b>3</b>A, multiple iterations of training-pruning cycles is needed to prevent IMP from suffering layer-collapse. Further, as shown in FIG. <b>3</b>B, the average square magnitude scores per layer, originally at initialization (blue), converge through training towards a linear relationship with the inverse layer size after training (pink), suggesting layer-wise conservation. In these figures, all data is from a VGG-19 model trained on CIFAR-10.

Gradient Descent Encourages Conservation

To better understand the dynamics of the IMP algorithm during training, a differentiable score

𝒮
   ⁡
   (
   
    θ
    i
   
   )
  
  =
  
   
    1
    2
   
   ⁢
   
    θ
    i
    2
   
  
 


<br/>
is considered that is algorithmically equivalent to the magnitude score. Consider these scores throughout training with gradient descent on a loss function L using an infinitesimal step size (i.e. gradient flow). In this setting, the temporal derivative of the parameters is equivalent to

d
     ⁢
     θ
    
    dt
   
   =
   
    -
    
     
      ∂
       
      ℒ
     
     
      ∂
       
      θ
     
    
   
  
  ,
 


<br/>
and thus the temporal derivative of the score is:

d
    dt
   
   ⁢
   
    1
    2
   
   ⁢
   
    θ
    i
    2
   
  
  =
  
   
    
     
      d
      ⁢
      
       θ
       i
      
     
     dt
    
    ⊙
    
     θ
     i
    
   
   =
   
    -
    
     
      
       ∂
        
       ℒ
      
      
       d
       ⁢
       
        θ
        i
       
      
     
     ⊙
     
      θ
      i

Surprisingly, this is a form of synaptic saliency and thus the neuron-wise and layer-wise conservation laws described above apply. In particular, this implies that for any two layers l and k of a simple, fully connected network, then:

d
    
     d
     ⁢
     t
    
   
   ⁢
   
    
     
     
      W
      
       [
       l
       ]
      
     
     
    
    F
    2
   
  
  =
  
   
    d
    dt
   
   ⁢
   
    
     
     
      W
      
       [
       k
       ]
      
     
     
    
    F
    2

This invariance has been noticed before by [45] as a form of implicit regularization and used to explain the empirical phenomenon that trained multi-layer models can have similar layer-wise magnitudes. In the context of pruning, this phenomenon implies that gradient descent training, with a small enough learning rate, encourages the squared magnitude scores to converge to an approximate layer-wise conservation, as shown in FIG. <b>3</b>B.

Conservation and Iterative Pruning Avoids Layer-Collapse

As explained above, conservation alone leads to layer-collapse by assigning parameters in the largest layers with lower scores relative to parameters in smaller layers. However, if conservation is coupled with iterative pruning, then when the largest layer is pruned, becoming smaller, then in subsequent iterations the remaining parameters of this layer will be assigned higher relative scores. With sufficient iterations, conservation coupled with iteration leads to a self-balancing pruning strategy allowing IMP to avoid layer-collapse. This insight on the importance of conservation and iteration applies more broadly to other algorithms with exact or approximate conservation properties (e.g. Skeletonization, SNIP, and GraSP as demonstrated above. Indeed, very recent work empirically confirms that iteration improves the performance of SNIP [46].

One or More Embodiments of the SynFlow System

FIG. <b>4</b> illustrates an example of a computing device <b>400</b> that may generate a highly sparse trainable subnetworks at initialization using a novel SynFlow process and utilize the highly sparse trainable subnetworks. It should be understood that the SynFlow process may also be implemented using cloud computing services, a mainframe computer, a client server architecture, a laptop computer and/or even a smartphone device that has sufficient processing power to perform the SynFlow process and then be able to implement the trainable highly sparse neural network generated by the SynFlow process.

In the example in FIG. <b>4</b>, the computing device <b>400</b> has a display <b>402</b> and a chassis/body <b>404</b> that houses one or more processors <b>406</b> that are interconnected to memory <b>408</b> and a store device <b>412</b>. In the example shown in FIG. <b>4</b>, a SynFlow process <b>410</b> is implemented as a plurality of lines of instructions that reside in the store <b>412</b> or memory <b>408</b> and are executed by the one or more processors <b>406</b> that are then configured to perform the SynFlow process as described below. In alternative embodiments, the SynFlow process may be implemented in a hardware device (FPGA, state machine, integrated circuit) that also perform the SynFlow process as described below. When the SynFlow process <b>410</b> is implemented in software, the code/instructions may be stored in the store <b>412</b> along with the neural network data and possible the data being analyzed using the trainable highly sparse neural network that results from the SynFlow process <b>410</b>. The computing device may further have input/output devices <b>414</b>, <b>416</b> (such as the keyboard <b>414</b> that may be a physical keyboard or a virtual keyboard on a touchscreen, etc., and the mouse <b>416</b>) that permit the user of the computing device <b>400</b> to interact with the SynFlow process <b>410</b> and the resultant trainable highly sparse neural network.

The SynFlow process <b>410</b> may implement an iterative synaptic flow neural network pruning process (“SynFlow”) that generates the trainable, highly sparse neural network with a high level of compression that does not suffer layer collapse. Furthermore, the SynFlow process <b>410</b> can be performed at initialization and without any training so that the SynFlow process is data agnostic. In addition to generating the trainable, highly sparse neural network, the system <b>400</b> shown in FIG. <b>4</b> may use the trainable, highly sparse neural network to perform data processing operations of piece of data in the same manner that a typical neural network would do.

FIG. <b>5</b> illustrates more details of an implementation of the SynFlow system <b>410</b>. As described above the elements <b>510</b>, <b>512</b> shown in FIG. <b>5</b> of the SynFlow system <b>410</b> may be implemented in software (plurality of lines of code/instructions executed on a processor so that the processor is configured to perform the processes or hardware. As shown in FIG. <b>5</b>, the SynFlow system <b>410</b> may include a neural network engine <b>510</b> that is connected to an iterative synaptic flow pruning tool <b>512</b> as shown. The neural network engine <b>510</b> may store an incoming original neural network to be pruned and pass the incoming original neural network onto the iterative synaptic flow pruning tool <b>512</b>. The iterative synaptic flow pruning tool <b>512</b> then performs the iterative synaptic flow pruning process (SynFlow) on the incoming original neural network to generate the trainable, highly sparse sub-network neural network without training data or data sets and without training the neural network so that the SynFlow process is data agnostic. Furthermore, the output of the SynFlow process <b>410</b> is trainable since the SynFlow process <b>410</b>, regardless of compression ratio, does not suffer from layer collapse while compression the neural network.

A Data-Agnostic Algorithm Satisfying Maximal Critical Compression

As discussed above, two attributes of the known Magnitude method to avoid layer-collapse include: (i) approximate layer-wise conservation of the pruning scores, and (ii) the iterative re-evaluation of these scores. While these properties allow the Magnitude method to identify high performing and highly sparse, trainable neural networks, the Magnitude method requires an impractical amount of computation to obtain them and thus the known Magnitude method has a technical problem of the impractical amount of computation. The SynFlow method provides a technical solution to this technical problem by providing a more efficient pruning method that does not require the impractical amount of computation.

The SynFlow method avoids layer-collapse and provably attains Maximal Critical Compression as shown by the below theorem whose proof is shown in Appendix A that forms part of the specification.

Theorem 3—Iterative, positive, conservative scoring achieves Maximal Critical Compression—If a pruning algorithm, with global-masking, assigns positive scores that respect layer-wise conservation and if the algorithm re-evaluates the scores every time a parameter is pruned, then the algorithm satisfies the Maximal Critical Compression axiom.

The Iterative Synaptic Flow Pruning (SynFlow) Method

The theorem above directly motivates the design of SynFlow, that provably reaches Maximal Critical Compression. First, the necessity for iterative score evaluation discourages algorithms that involve backpropagation on batches of data, and instead motivates the development of an efficient data-independent scoring procedure. Second, positivity and conservation motivates the construction of a loss function that yields positive synaptic saliency scores. These insights are combined to introduce a new loss function (where  is the all ones vector and |θ<sup>[l]</sup>| is the element-wise absolute value of parameters in the l<sup>th </sup>layer),

ℛ
   
    S
    ⁢
    F
   
  
  =
  
   
        T
   
   
    (
    
     
      ∏
      
       l
       =
       1
      
      L
     
      
     
      
       ❘
       "\[LeftBracketingBar]"
      
      
       θ
       
        [
        l
        ]
       
      
      
       ❘
       "\[RightBracketingBar]"
      
     
    
    )
   
     
 


<br/>
that yields the positive, synaptic saliency scores

(
  
   
    
     ∂
      
     
      ℛ
      SF
     
    
    
     ∂
      
     θ
    
   
   ⊙
   θ
  
  )
 


<br/>
called Synaptic Flow. For a simple, fully connected network (i.e. f(x)=W<sup>[N]</sup> . . . W<sup>[1]</sup>x), the Synaptic Flow score for a parameter $w<sup>[l]</sup><sub>ij </sub>may be factored as

𝒮
    SF
   
   (
   
    w
    ij
    
     [
     l
     ]
    
   
   )
  
  =
  
   
    
     [
     
      
              T
      
      
       
        ∏
        
         k
         =
         
          l
          +
          1
         
        
        N
       
       
        
         ❘
         "\[LeftBracketingBar]"
        
        
         W
         
          [
          k
          ]
         
        
        
         ❘
         "\[RightBracketingBar]"
        
       
      
     
     ]
    
    i
   
   ⁢
   
    
     
      
       ❘
       "\[LeftBracketingBar]"
      
      
       w
       ij
       
        [
        l
        ]
       
      
      
       ❘
       "\[RightBracketingBar]"
      
     
     [
     
      
       ∏
       
        k
        =
        1
       
       
        l
        -
        1
       
      
       
      
       
        
         ❘
         "\[LeftBracketingBar]"
        
        
         W
         
          [
          k
          ]
         
        
        
         ❘
         "\[RightBracketingBar]"
        
       
             
     
     ]
    
    j

This perspective demonstrates that Synaptic Flow score is a generalization of magnitude score (|w<sub>ij</sub><sup>[l]</sup>|), where the scores consider the product of synaptic strengths flowing through each parameter, taking the inter-layer interactions of parameters into account. The Synaptic Flow score in the Iterative Synaptic Flow Pruning (SynFlow) method shown in FIGS. <b>6</b> and <b>7</b> and now described in more detail.

FIG. <b>6</b> illustrates an iterative snaptic flow pruning method <b>600</b> and FIG. <b>7</b> is an example of the pseudcode for the iterative snaptic flow pruning method. In one embodiment, the method <b>600</b> is performed by the system shown in FIGS. <b>4</b> and <b>5</b>, but may also be performed on other systems and in other environments that are within the scope of this disclosure. Once the method receives the initial neural network with its neurons and synapses, the method initializes the binary mask (<b>602</b>). As shown in the pseudocode example in FIG. <b>7</b>, the input may by a neural network f(x; θ<sub>0</sub>), a compression ratio ρ and iterations n. Unlike other known pruning methods, the SynFlow method requires only one additional hyperparameter, the number of pruning iterations n.

The method may check to see if there are more iteration steps (<b>604</b>) and, if there are no more iteration steps (meaning that the method has been completed to generate the trainable, highly sparse neural network), the method returns/outputs a masked network that is the trainable, highly sparse neural network (<b>605</b>). A trainable, highly sparse neural network is a neural network having less than 10% of the original number of parameters remaining after the pruning. If there are additional iteration steps, the method mask parameters (<b>606</b>) of neurons of the neural network. During the masking process (<b>606</b>), the method scores the parameters of a network according to some metric, such as the Synflow score/metric discussed above, and masks the parameters (removes or keeps the parameter) according to their scores. In this method, the method may evaluate the Synflow objective (<b>608</b>) and then computes a Synflow score (<b>610</b>) as discussed above. The method may then find the threshold (<b>612</b>) for each parameter and determine if each parameter meets the threshold and the updates the mask (<b>614</b>) with the parameters that meet the threshold. As shown in FIG. <b>7</b>, the threshold, given the desired sparsity of parameters, the automatically determined by the process

(
  
   τ
   ←
   
    (
    
     1
     -
     
      ρ
      
       -
       
        k
        n
       
      
     
    
    )
   
  
 


<br/>
percentile of S) where S is the Synflow score. Thus, the threshold is a percentile of the Synflow score that is determined based on the desired reduced parameters for the trainable, highly sparse neural network being produced.

The method then loops back to determine if there are more iteration steps. In this manner, the method <b>600</b> generates the trainable, highly sparse neural network. As detailed in the attached Appendix A (Hyperparameters), it is shown that an exponential pruning schedule (ρ<sup>−k/n</sup>) with n=100 pruning iterations essentially prevents layer-collapse whenever avoidable (for example see FIG. <b>8</b> described below), while remaining computationally feasible, even for large networks.

FIG. <b>8</b> shows a compression ratio of various known pruning processes as compared to the SynFlow method. FIG. <b>8</b> shows the Top-1 test accuracy as a function of the compression ratio for a VGG-16 model pruned at initialization and trained on CIFAR-100. The colored arrows along the horizontal axis represent the critical compression each corresponding pruning methods before collapse. As shown in FIG. <b>8</b>, the known random, Magnitude, SNIP and GraSP pruning methods all have their accuracy reduce to zero at compression ratios between 100 and 10000 meaning that all of the known methods suffer layer collapse and do not achieve a maximum compression ratio. In contrast, the SynFlow method (shown in FIGS. <b>6</b>-<b>7</b> and as the line with the diamond indicator in FIG. <b>8</b>) does not suffer layer collapse and achieves the maximum compression thus outputting the trainable, highly sparse neural network that is a technical solution to the technical problems of the known pruning methods. While FIG. <b>8</b> shows a maximum compression of 10<sup>6</sup>, each configuration of a deep learning model has its own corresponding maximum compression ratio as is known in the art and each maximum compression ratio ensures that at least one parameter remains per layer of the neural network.

As described above, FIG. <b>9</b> shows a layer collapse of various known pruning processes as compared to layer collapse of the SynFlow method. As shown, each of the known methods (random, Magnitude, SNIP and GraSP) suffer layer collapse (dotted lines) in certain layers and certain compression ratios and thus cannot produce a trainable highly sparse neural network which is a technical problem of the known pruning methods. In contrast, the SynFlow method described above does not suffer from layer collapse at any compression ratio as shown in FIG. <b>9</b> since none of the lines/layers in FIG. <b>9</b> are dotted. Thus, the SynFlow method provides a technical solution as described above that overcomes the technical problem of layer collapse of known pruning methods.

FIG. <b>10</b>A shows a neuron-wise conservation of score for various known pruning processes as compared to layer collapse of the SynFlow method and FIG. <b>10</b>B shows an inverse relationship between layer size and average layer score of various known pruning processes as compared to layer collapse of the SynFlow method as described above. As shown in these figures, unlike the known algorithms that do not provide exact neuron-wise conversation of score and a perfect linear relationship of the average score, the SynFlow method achieves both which shows the advantage of the SynFlow method over the known pruning methods.

Experiments

The SynFlow method described above and its performance (shown by the red line with the triangle identifier in FIG. <b>11</b>) may be empirically benchmarked against baseline random pruning and magnitude pruning as well as the state-of-the-art algorithms SNIP and GraSP (the other colored lines in FIG. <b>11</b>). FIG. <b>11</b> illustrates top-1 test accuracy as a function of different compression ratios for known pruning methods and the SynFlow method over twelve different models and datasets. The five methods (including SynFlow) were tested on 12 distinct combinations of modern architectures (VGG-11, VGG-16, ResNet-18, WideResNet-18) and datasets (CIFAR-10, CIFAR-100, Tiny ImageNet) over an exponential sweep of compression ratios (10<sup>α</sup> for α=[0, 0.25, . . . , 2.75, 3]). Appendix A contains more details and hyperparameters of the experiments results shown in FIG. <b>11</b>. For the testing whose results are shown in FIG. <b>11</b>, three runs were performed with the same hyperparameter conditions and different random seeds and the solid line represents the mean, the shaded region represents area between minimum and maximum performance of the three runs.

As shown in FIG. <b>11</b>, the SynFlow method (whose results for each dataset and architecture are shown with a red line with the triangle identifier) consistently outperforms the other methods in the high compression regime (10<sup>1.5</sup><ρ) and demonstrates significantly more stability, as indicated by its tight intervals. Furthermore, SynFlow is the only pruning method that reliably shows better performance to the random pruning baseline since SNIP and GraSP perform significantly worse than random pruning with ResNet-18 and WideResNet-18 trained on Tiny ImageNet as shown in FIG. <b>11</b>. In addition, the SynFlow method is also quite competitive in the low compression regime (ρ<10<sup>1.5</sup>) as shown in the lefthand portion of each chart that is blown up inside of the box. Although magnitude pruning can partially outperform SynFlow in this low compression regime with models trained on Tiny ImageNet, it suffers from catastrophic layer-collapse as indicated by the sharp drops in accuracy shown in FIG. <b>11</b>. While an exemplary number of iterations are discussed above, the number of iterations is user configurable, but as shown above 100 iterations achieves the goals of the Synflow method.

[1] Michael C Mozer and Paul Smolensky. Skeletonization: A technique for trimming the fat from a network via relevance assessment. In Advances in neural information processing systems, pages 107-115, 1989.
    [2] Yann LeCun, John S Denker, and Sara A Solla. Optimal brain damage. In Advances in neural information processing systems, pages 598-605, 1990.
    [3] Babak Hassibi and David G Stork. Second order derivatives for network pruning: Optimal brain surgeon. In Advances in neural information processing systems, pages 164-171, 1993.
    [4] Steven A Janowsky. Pruning versus clipping in neural networks. Physical Review A, 39(12):6600, 1989.
    [5] Russell Reed. Pruning algorithms-a survey. IEEE transactions on Neural Networks, 4(5):740-747, 1993.
    [6] Song Han, Jeff Pool, John Tran, and William Dally. Learning both weights and connections for efficient neural network. In Advances in neural information processing systems, pages 1135-1143, 2015.
    [7] Vivienne Sze, Yu-Hsin Chen, Tien-Ju Yang, and Joel S Emer. Efficient processing of deep neural networks: A tutorial and survey. Proceedings of the IEEE, 105(12):2295-2329, 2017.
    [8] Sanjeev Arora, Rong Ge, Behnam Neyshabur, and Yi Zhang. Stronger generalization bounds for deep nets via a compression approach. In Jennifer Dy and Andreas Krause, editors, Proceedings of the 35th International Conference on Machine Learning, volume 80 of Proceedings of Machine Learning Research, pages 254-263. PMLR, 2018.
    [9] Hidenori Tanaka, Aran Nayebi, Niru Maheswaranathan, Lane McIntosh, Stephen Baccus, and Surya Ganguli. From deep learning to mechanistic understanding in neuroscience: the structure of retinal prediction. In Advances in Neural Information Processing Systems, pages 8535-8545, 2019.
    [10] Jonathan Frankle and Michael Carbin. The lottery ticket hypothesis: Finding sparse, trainable neural networks. In International Conference on Learning Representations, 2019.
    [11] Jonathan Frankle, G Karolina Dziugaite, DM Roy, and M Carbin. Stabilizing the lottery ticket hypothesis. arXiv, page.
    [12] Ari Morcos, Haonan Yu, Michela Paganini, and Yuandong Tian. One ticket to win them all: generalizing lottery ticket initializations across datasets and optimizers. In Advances in Neural Information Processing Systems, pages 4933-4943, 2019.
    [13] Namhoon Lee, Thalaiyasingam Ajanthan, and Philip Torr. SNIP: SINGLE-SHOT NETWORK PRUNING BASED ON CONNECTION SENSITIVITY. In International Conference on Learning Representations, 2019.
    [14] Chaoqi Wang, Guodong Zhang, and Roger Grosse. Picking winning tickets before training by preserving gradient flow. In International Conference on Learning Representations, 2020.
    [15] Forrest N Iandola, Song Han, Matthew W Moskewicz, Khalid Ashraf, William J Dally, and Kurt Keutzer. Squeezenet: Alexnet-level accuracy with 50× fewer parameters and <0.5 mb model size. arXiv preprint arXiv:1602.07360, 2016.
    [16] Andrew G Howard, Menglong Zhu, Bo Chen, Dmitry Kalenichenko, Weijun Wang, Tobias Weyand, Marco Andreetto, and Hartwig Adam. Mobilenets: Efficient convolutional neural networks for mobile vision applications. arXiv preprint arXiv:1704.04861, 2017.
    [17] Ameya Prabhu, Girish Varma, and Anoop Namboodiri. Deep expander networks: Efficient deep networks from graph theory. In Proceedings of the European Conference on Computer Vision (ECCV), pages 20-35, 2018.
    [18] Max Jaderberg, Andrea Vedaldi, and Andrew Zisserman. Speeding up convolutional neural networks with low rank expansions. In Proceedings of the British Machine Vision Conference. BMVA Press, 2014. doi: http://dx.doi.org/10.5244/C.28.88.
    [19] Alexander Novikov, Dmitrii Podoprikhin, Anton Osokin, and Dmitry P Vetrov. Tensorizing neural networks. In Advances in neural information processing systems, pages 442-450, 2015.
    [20] Guillaume Bellec, David Kappel, Wolfgang Maass, and Robert Legenstein. Deep rewiring: Training very sparse deep networks. In International Conference on Learning Representations, 2018.
    [21] Decebal Constantin Mocanu, Elena Mocanu, Peter Stone, Phuong H Nguyen, Madeleine Gibescu, and Antonio Liotta. Scalable training of artificial neural networks with adaptive sparse connectivity inspired by network science. Nature communications, 9(1):1-12, 2018.
    [22] Trevor Gale, Erich Elsen, and Sara Hooker. The state of sparsity in deep neural networks. arXiv preprint arXiv:1902.09574, 2019.
    [23] Davis Blalock, Jose Javier Gonzalez Ortiz, Jonathan Frankle, and John Guttag. What is the state of neural network pruning?arXiv preprint arXiv:2003.03033, 2020.
    [24] Sejun Park*, Jaeho Lee*, Sangwoo Mo, and Jinwoo Shin. Lookahead: A far-sighted alternative of magnitude-based pruning. In International Conference on Learning Representations, 2020.
    [25] Ehud D Karnin. A simple procedure for pruning back-propagation trained neural networks. IEEE transactions on neural networks, 1(2):239-242, 1990.
    [26] Pavlo Molchanov, Stephen Tyree, Tero Karras, Timo Aila, and Jan Kautz. Pruning convolutional neural networks for resource efficient inference. arXiv preprint arXiv:1611.06440, 2016.
    [27] Pavlo Molchanov, Arun Mallya, Stephen Tyree, Iuri Frosio, and Jan Kautz. Importance estimation for neural network pruning. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 11264-11272, 2019.
    [28] Yiwen Guo, Anbang Yao, and Yurong Chen. Dynamic network surgery for efficient dnns. In Advances in neural information processing systems, pages 1379-1387, 2016.
    [29] Xin Dong, Shangyu Chen, and Sinno Pan. Learning to prune deep neural networks via layer-wise optimal brain surgeon. In Advances in Neural Information Processing Systems, pages 4857-4867, 2017.
    [30] Ruichi Yu, Ang Li, Chun-Fu Chen, Jui-Hsin Lai, Vlad I Morariu, Xintong Han, Mingfei Gao, Ching-Yung Lin, and Larry S Davis. Nisp: Pruning networks using neuron importance score propagation. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 9194-9203, 2018.
    [31] Zhuang Liu, Mingjie Sun, Tinghui Zhou, Gao Huang, and Trevor Darrell. Rethinking the value of network pruning. In International Conference on Learning Representations, 2019.
    [32] Namhoon Lee, Thalaiyasingam Ajanthan, Stephen Gould, and Philip H. S. Torr. A signal propagation perspective for pruning neural networks at initialization. In International Conference on Learning Representations, 2020.
    [33] Haoran You, Chaojian Li, Pengfei Xu, Yonggan Fu, Yue Wang, Xiaohan Chen, Richard G. Baraniuk, Zhangyang Wang, and Yingyan Lin. Drawing early-bird tickets: Toward more efficient training of deep networks. In International Conference on Learning Representations, 2020.
    [34] Wenyuan Zeng and Raquel Urtasun. Mlprune: Multi-layer pruning for automated neural network compression. 2018.
    [35] Hesham Mostafa and Xin Wang. Parameter efficient training of deep convolutional neural networks by dynamic sparse reparameterization. In Proceedings of the 36th International Conference on Machine Learning, volume 97 of Proceedings of Machine Learning Research, pages 4646-4655. PMLR, 2019.
    [36] Xavier Glorot and Yoshua Bengio. Understanding the difficulty of training deep feedforward neural networks. In Proceedings of the thirteenth international conference on artificial intelligence and statistics, pages 249-256, 2010.
    [37] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In Proceedings of the IEEE conference on computer vision and pattern recognition, pages 770-778, 2016.
    [38] Kedar Dhamdhere, Mukund Sundararajan, and Qiqi Yan. How important is a neuron. In International Conference on Learning Representations, 2019.
    [39] Sebastian Bach, Alexander Binder, Grégoire Montavon, Frederick Klauschen, Klaus-Robert Müller, and Wojciech Samek. On pixel-wise explanations for non-linear classifier decisions by layer-wise relevance propagation. PloS one, 10(7), 2015.
    [40] Seul-Ki Yeom, Philipp Seegerer, Sebastian Lapuschkin, Simon Wiedemann, Klaus-Robert Müller, and Wojciech Samek. Pruning by explaining: A novel criterion for deep neural network pruning. arXiv preprint arXiv:1912.08881, 2019.
    [41] Hattie Zhou, Janice Lan, Rosanne Liu, and Jason Yosinski. Deconstructing lottery tickets: Zeros, signs, and the supermask. In Advances in Neural Information Processing Systems, pages 3592-3602, 2019.
    [42] Haoran You, Chaojian Li, Pengfei Xu, Yonggan Fu, Yue Wang, Xiaohan Chen, Richard G. Baraniuk, Zhangyang Wang, and Yingyan Lin. Drawing early-bird tickets: Toward more efficient training of deep networks. In International Conference on Learning Representations, 2020.
    [43] Jonathan Frankle, Gintare Karolina Dziugaite, Daniel M Roy, and Michael Carbin. Linear mode connectivity and the lottery ticket hypothesis. arXiv preprint arXiv:1912.05671, 2019.
    [44] Haonan Yu, Sergey Edunov, Yuandong Tian, and Ari S. Morcos. Playing the lottery with rewards and multiple languages: lottery tickets in rl and nlp. In International Conference on Learning Representations, 2020.
    [45] Simon S Du, Wei Hu, and Jason D Lee. Algorithmic regularization in learning deep homogeneous models: Layers are automatically balanced. In Advances in Neural Information Processing Systems, pages 384-395, 2018.
    [46] Stijn Verdenius, Maarten Stol, and Patrick Forré. Pruning via iterative ranking of sensitivity statistics. arXiv preprint arXiv:2006.00896, 2020.

The foregoing description, for purpose of explanation, has been with reference to specific embodiments. However, the illustrative discussions above are not intended to be exhaustive or to limit the disclosure to the precise forms disclosed. Many modifications and variations are possible in view of the above teachings. The embodiments were chosen and described in order to best explain the principles of the disclosure and its practical applications, to thereby enable others skilled in the art to best utilize the disclosure and various embodiments with various modifications as are suited to the particular use contemplated.

The system and method disclosed herein may be implemented via one or more components, systems, servers, appliances, other subcomponents, or distributed between such elements. When implemented as a system, such systems may include and/or involve, inter alia, components such as software modules, general-purpose CPU, RAM, etc. found in general-purpose computers. In implementations where the innovations reside on a server, such a server may include or involve components such as CPU, RAM, etc., such as those found in general-purpose computers.

Additionally, the system and method herein may be achieved via implementations with disparate or entirely different software, hardware and/or firmware components, beyond that set forth above. With regard to such other components (e.g., software, processing components, etc.) and/or computer-readable media associated with or embodying the present inventions, for example, aspects of the innovations herein may be implemented consistent with numerous general purpose or special purpose computing systems or configurations.

Various exemplary computing systems, environments, and/or configurations that may be suitable for use with the innovations herein may include, but are not limited to: software or other components within or embodied on personal computers, servers or server computing devices such as routing/connectivity components, hand-held or laptop devices, multiprocessor systems, microprocessor-based systems, set top boxes, consumer electronic devices, network PCs, other existing computer platforms, distributed computing environments that include one or more of the above systems or devices, etc.

In some instances, aspects of the system and method may be achieved via or performed by logic and/or logic instructions including program modules, executed in association with such components or circuitry, for example. In general, program modules may include routines, programs, objects, components, data structures, etc. that perform particular tasks or implement particular instructions herein. The inventions may also be practiced in the context of distributed software, computer, or circuit settings where circuitry is connected via communication buses, circuitry or links. In distributed settings, control/instructions may occur from both local and remote computer storage media including memory storage devices.

The software, circuitry and components herein may also include and/or utilize one or more type of computer readable media. Computer readable media can be any available media that is resident on, associable with, or can be accessed by such circuits and/or computing components. By way of example, and not limitation, computer readable media may comprise computer storage media and communication media. Computer storage media includes volatile and nonvolatile, removable and non-removable media implemented in any method or technology for storage of information such as computer readable instructions, data structures, program modules or other data. Computer storage media includes, but is not limited to, RAM, ROM, EEPROM, flash memory or other memory technology, CD-ROM, digital versatile disks (DVD) or other optical storage, magnetic tape, magnetic disk storage or other magnetic storage devices, or any other medium which can be used to store the desired information and can accessed by computing component. Communication media may comprise computer readable instructions, data structures, program modules and/or other components. Further, communication media may include wired media such as a wired network or direct-wired connection, however no media of any such type herein includes transitory media. Combinations of the any of the above are also included within the scope of computer readable media.

In the present description, the terms component, module, device, etc. may refer to any type of logical or functional software elements, circuits, blocks and/or processes that may be implemented in a variety of ways. For example, the functions of various circuits and/or blocks can be combined with one another into any other number of modules. Each module may even be implemented as a software program stored on a tangible memory (e.g., random access memory, read only memory, CD-ROM memory, hard disk drive, etc.) to be read by a central processing unit to implement the functions of the innovations herein. Or, the modules can comprise programming instructions transmitted to a general-purpose computer or to processing/graphics hardware via a transmission carrier wave. Also, the modules can be implemented as hardware logic circuitry implementing the functions encompassed by the innovations herein. Finally, the modules can be implemented using special purpose instructions (SIMD instructions), field programmable logic arrays or any mix thereof which provides the desired level performance and cost.

As disclosed herein, features consistent with the disclosure may be implemented via computer-hardware, software, and/or firmware. For example, the systems and methods disclosed herein may be embodied in various forms including, for example, a data processor, such as a computer that also includes a database, digital electronic circuitry, firmware, software, or in combinations of them. Further, while some of the disclosed implementations describe specific hardware components, systems and methods consistent with the innovations herein may be implemented with any combination of hardware, software and/or firmware. Moreover, the above-noted features and other aspects and principles of the innovations herein may be implemented in various environments. Such environments and related applications may be specially constructed for performing the various routines, processes and/or operations according to the invention or they may include a general-purpose computer or computing platform selectively activated or reconfigured by code to provide the necessary functionality. The processes disclosed herein are not inherently related to any particular computer, network, architecture, environment, or other apparatus, and may be implemented by a suitable combination of hardware, software, and/or firmware. For example, various general-purpose machines may be used with programs written in accordance with teachings of the invention, or it may be more convenient to construct a specialized apparatus or system to perform the required methods and techniques.

Aspects of the method and system described herein, such as the logic, may also be implemented as functionality programmed into any of a variety of circuitry, including programmable logic devices (“PLDs”), such as field programmable gate arrays (“FPGAs”), programmable array logic (“PAL”) devices, electrically programmable logic and memory devices and standard cell-based devices, as well as application specific integrated circuits. Some other possibilities for implementing aspects include: memory devices, microcontrollers with memory (such as EEPROM), embedded microprocessors, firmware, software, etc.

Furthermore, aspects may be embodied in microprocessors having software-based circuit emulation, discrete logic (sequential and combinatorial), custom devices, fuzzy (neural) logic, quantum devices, and hybrids of any of the above device types. The underlying device technologies may be provided in a variety of component types, e.g., metal-oxide semiconductor field-effect transistor (“MOSFET”) technologies like complementary metal-oxide semiconductor (“CMOS”), bipolar technologies like emitter-coupled logic (“ECL”), polymer technologies (e.g., silicon-conjugated polymer and metal-conjugated polymer-metal structures), mixed analog and digital, and so on.

It should also be noted that the various logic and/or functions disclosed herein may be enabled using any number of combinations of hardware, firmware, and/or as data and/or instructions embodied in various machine-readable or computer-readable media, in terms of their behavioral, register transfer, logic component, and/or other characteristics. Computer-readable media in which such formatted data and/or instructions may be embodied include, but are not limited to, non-volatile storage media in various forms (e.g., optical, magnetic or semiconductor storage media) though again does not include transitory media. Unless the context clearly requires otherwise, throughout the description, the words “comprise,” “comprising,” and the like are to be construed in an inclusive sense as opposed to an exclusive or exhaustive sense; that is to say, in a sense of “including, but not limited to.” Words using the singular or plural number also include the plural or singular number respectively. Additionally, the words “herein,” “hereunder,” “above,” “below,” and words of similar import refer to this application as a whole and not to any particular portions of this application. When the word “or” is used in reference to a list of two or more items, that word covers all of the following interpretations of the word: any of the items in the list, all of the items in the list and any combination of the items in the list.

Although certain presently preferred implementations of the invention have been specifically described herein, it will be apparent to those skilled in the art to which the invention pertains that variations and modifications of the various implementations shown and described herein may be made without departing from the spirit and scope of the invention. Accordingly, it is intended that the invention be limited only to the extent required by the applicable rules of law.

While the foregoing has been with reference to a particular embodiment of the disclosure, it will be appreciated by those skilled in the art that changes in this embodiment may be made without departing from the principles and spirit of the disclosure, the scope of which is defined by the appended claims.

## Claims

1. An apparatus, comprising:
a computer system having an application specific integrated circuit (ASIC) and memory and a plurality of lines of instructions executed by the ASIC to perform operations comprising:
receive an untrained initial neural network having one or more layers with an input layer, an output layer and one or more layers between the input layer and the output layer in which each layer has a plurality of neurons with each neuron having a parameter, a particular neuron in each layer having a synapse that connects to another particular neuron in a different layer of the initial neural network;
initialize a binary mask that prunes one or more neurons in the initial neural network; and
perform iterative synaptic flow pruning to generate a sparse trainable subnetwork with a predetermined level of compression and no layer collapse.

2. The apparatus of claim 1, wherein the ASIC is further configured to generate a score for each parameter, prune any neuron of the initial neural network whose score does not meet a threshold to generate an updated mask and iteratively generate the score and pruning the one or more neurons until a predetermined number of iterations has been completed.

3. The apparatus of claim 2, wherein the ASIC is further configured to generate a synaptic saliency score.

4. The apparatus of claim 3, wherein the ASIC is further configured to generate a positive synaptic saliency score.

5. A method, comprising:
receiving, by an application specific integrated circuit (ASIC), an untrained initial neural network having one or more layers with an input layer, an output layer and one or more layers between the input layer and the output layer in which each layer has a plurality of neurons with each neuron having a parameter, a particular neuron in each layer having a synapse that connects to another particular neuron in a different layer of the initial neural network;
initializing, by the ASIC, a binary mask that prunes one or more neurons in the initial neural network; and
performing, by the ASIC, iterative synaptic flow pruning to generate a sparse trainable subnetwork with a predetermined level of compression and no layer collapse.

6. The method of claim 5, wherein performing the iterative synaptic flow pruning further comprises:
generating, by the ASIC, a score for each parameter;
pruning, by the ASIC, any neuron of the initial neural network whose score does not meet a threshold to generate an updated mask; and
iteratively generating, by the ASIC, the score and pruning the one or more neurons until a predetermined number of iterations has been completed.

7. The method of claim 6, wherein the generating the score further comprises generating, by the ASIC, a synaptic saliency score.

8. The method of claim 7, wherein the generating the score further comprises generating, by the ASIC, a positive synaptic saliency score.

9. An apparatus, comprising:
a computer system having an application specific integrated circuit (ASIC) and memory and a plurality of lines of instructions executed by the ASIC to perform operations comprising:
receive an untrained initial neural network having one or more layers with an input layer, an output layer and one or more layers between the input layer and the output layer in which each layer has a plurality of neurons with each neuron having a parameter, a particular neuron in each layer having a synapse that connects to another particular neuron in a different layer of the initial neural network;
generate a sparse trainable subnetwork with a predetermined level of compression and no layer collapse using iterative synaptic pruning; and
use the sparse trainable subnetwork for data processing.

10. The apparatus of claim 9, wherein the ASIC is further configured to generate a score for each parameter, prune any neuron of the initial neural network whose score does not meet a threshold to generate an updated mask and iteratively generate the score and pruning the neurons until a predetermined number of iterations has been completed to generate the sparse trainable subnetwork.

11. The apparatus of claim 10, wherein the ASIC is further configured to generate a synaptic saliency score.

12. The apparatus of claim 11, wherein the ASIC is further configured to generate a positive synaptic saliency score.

13. A method, comprising:
receiving, by an application specific integrated circuit (ASIC), an untrained initial neural network having one or more layers with an input layer, an output layer and one or more layers between the input layer and the output layer in which each layer has a plurality of neurons with each neuron having a parameter, a particular neuron in each layer having a synapse that connects to another particular neuron in a different layer of the initial neural network;
generating, by the ASIC, a sparse trainable subnetwork with a predetermined level of compression and no layer collapse using iterative synaptic pruning; and
using, by the ASIC, the sparse trainable subnetwork for data processing.

14. The method of claim 13, wherein generating the sparse trainable subnetwork further comprises:
generating, by the ASIC, a score for each parameter;
pruning, by the ASIC, any neuron of the initial neural network whose score does not meet a threshold to generate an updated mask; and
iteratively generating, by the ASIC, the score and pruning the neurons until a predetermined number of iterations has been completed.

15. The method of claim 14, wherein the generating the score further comprises generating, by the ASIC, a synaptic saliency score.

16. The method of claim 15, wherein the generating the score further comprises generating, by the ASIC, a positive synaptic saliency score.

