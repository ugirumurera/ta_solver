# Description #
This a general software framework for solving traffic assignment problems, both static and dynamic, utilizing the [BeATS API](https://bitbucket.org/gcgomes/beats-sim) to encode traffic scenarios. 

# SET UP #

**Step 1.** Install the [JAVA 8](http://www.oracle.com/technetwork/java/javase/downloads/index.html) JDK on your computer.
[This](https://www.java.com/en/download/help/version_manual.xml) will show you how to check your current version of JAVA.

**Step 2.** Install Python on your system if not already installed. Codes was developed with Python 2.7.

** Step 3.** Install [Python-igraph](http://igraph.org/python/#pyinstall). This library is necessary to validate the installation. It solves a small static traffic assignment problem using the Frank-Wolfe algorithm.

**Step 4.** Send an email to Gabriel Gomes (gomes@path.berkeley.edu) requesting access to the BeATS Dropbox folder. Please include your Dropbox user name. This folder contains a jar file named py4jbeats-1.0-SNAPSHOT-jar-with-dependencies.jar. This file includes the BeATS API and a utility called py4j which establishes a connection between Python and Java. You should have Dropbox sync this folder with your computer so that you always have the latest version of the BeATS API.

**Step 5.** Run Test to validate installation:

* On Windows: Run **Test_on_Windows.py**
* On Linux/MacOS: Run **Test_on_Linux.py**

This will initialize a small instance of the static traffic assignment problem and solve it using the Frank-Wolfe algorithm. 

It will print "Installation Successful!" to the console if everything goes well. 

# Contacts #

* **Juliette Ugirumurera**: julymurera@gmail.com
* **Gabriel Gomes**: gomes@path.berkeley.edu

# Description #

The goal of this project is to establish an interface between the traffic modeling and the numerical sides of the traffic assignment problem. The intended users are the modelers. 

To use the system, you must implement three things:
1. A link state data class. This is an implementation of the Traffic_States.Abstract_Traffic_State class. Objects of this class should hold state information for a single link of the network. If your model is multi-commodity, then all commodities should be included. 
2. A traffic model. This is an implementation of Traffic_Models.Abstract_Traffic_Model. 
3. A link cost function. This is an implementation of Cost_Functions.Abstract_Cost_Function. 

## Architecture ##

Below is a diagram of the assumed data flow. The algorithms team (lead by Juliette) is in charge of the SOLVER, which includes numerical methods for convex optimization problems and variational inequalities, running in the HPC environment. 

![Picture1.png](https://bitbucket.org/repo/5q9q4pE/images/1708996569-Picture1.png)

The generic SOLVER works in a loop in which it generates candidate demand assignments, and expects to be given the corresponding network cost trajectory (`trajectory' here means trajectory in time). This loop continues until an equilibrium demand assignment is reached. 

In addition to evaluating the traffic model and link cost functions, there are additional methods which, if implemented, may increase the efficiency of the solver. 

* Symmetry: If the Jacobian of the demand-to-cost function is symmetric, then the solver may use a convex optimization problem to find the solution. Set the `is_symmetric' flag of the traffic model and the cost functions to 'True' if you want this to happen. 

* Antiderivative: If convex optimization is used, then the cost function of the optimization problem will be the antiderivative of the demand-to-cost function. Some numerical algorithms will require this information. To use these algorithms, you should implement the "evaluate_Antiderivative" method of the cost function. 

* Gradient: Similarly with the gradient of both the cost function and the traffic model. 

Some solvers (e.g. Frank-Wolfe) will take adv



## Data classes ##


![Picture2.png](https://bitbucket.org/repo/5q9q4pE/images/2822392912-Picture2.png)