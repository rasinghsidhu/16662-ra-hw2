import numpy
import matplotlib.pyplot as pl
import math
import time
import random

class SimpleEnvironment(object):
	
	def __init__(self, herb):
		self.robot = herb.robot
		self.boundary_limits = [[-5., -5.], [5., 5.]]

		# add an obstacle
		table = self.robot.GetEnv().ReadKinBodyXMLFile('models/objects/table.kinbody.xml')
		self.robot.GetEnv().Add(table)

		table_pose = numpy.array([[ 0, 0, -1, 1.0], 
								  [-1, 0,  0, 0], 
								  [ 0, 1,  0, 0], 
								  [ 0, 0,  0, 1]])
		table.SetTransform(table_pose)

		# goal sampling probability
		self.p = 0.0

	def SetGoalParameters(self, goal_config, p = 0.2):
		self.goal_config = goal_config
		self.p = p
		
	def GenerateRandomConfiguration(self):
		config = [0] * 2;
		lower_limits, upper_limits = self.boundary_limits

		import numpy
		lower_limits = numpy.array(lower_limits)
		upper_limits = numpy.array(upper_limits)

		choice = numpy.random.rand(1)
		if choice < self.p:
			config = self.goal_config
		else:
			COLLISION = True	
			while COLLISION:
				config = numpy.random.rand(2)*(upper_limits - lower_limits) + lower_limits
				# Check if it is collision free
				with self.robot:
					robot_pos = self.robot.GetTransform()
					robot_pos[0:2,3] = config
					self.robot.SetTransform(robot_pos)
					if self.robot.GetEnv().CheckCollision(self.robot) == False:
						COLLISION = False
		return numpy.array(config)

	def ComputeDistance(self, start_config, end_config):
		return numpy.linalg.norm(end_config - start_config)


	def Extend(self, start_config, end_config):
		#number of steps
		epsilon = .01
		dist = self.ComputeDistance(start_config, end_config)
		numSteps = math.ceil(dist / epsilon)
		step = (end_config - start_config) / numSteps
		best_config = None
		i = 1
		while i <= numSteps:
			cur_config = start_config+step*i
			# Check if it is collision free
			with self.robot:
				robot_pos = self.robot.GetTransform()
				robot_pos[0:2,3] = cur_config
				self.robot.SetTransform(robot_pos)
				if self.robot.GetEnv().CheckCollision(self.robot) == True:
					return best_config
			#update variables
			best_config = cur_config
			i += 1
		return end_config

	def ShortenPath(self, path, timeout=5.0):
		print('starting path shortening')
		start_time = time.time()

		current_time = 0
		p1 = [0,0]
		p2 = [0,0]
		i = 0
		while current_time < timeout and i == 0:
			# print("NOW IN THE FUNCTION LOOP")
			badIndeces = []
			pathLength = len(path)
			p1index = random.randint(0,pathLength-2)
			p2index = p1index
			while p2index == p1index or abs(p2index-p1index) <= 1:
				p2index = random.randint(0,pathLength-2)
			if p1index > p2index:
				p1index, p2index = p2index,p1index
			# print(p1index)
			# print(p2index)
			# print(pathLength)
			p1a = numpy.array(path[p1index])
			p1b = numpy.array(path[p1index+1])
			p2a = numpy.array(path[p2index])
			p2b = numpy.array(path[p2index+1])  
			

			#choose random interpolation between points
			p1Vec = (p1b-p1a)
			p2Vec = (p2b-p2a)

			p1 = p1a + (p1Vec*random.random())
			p2 = p2a + (p2Vec*random.random())

			#TODO use extend to move to the two random points
			extender = self.Extend(p1,p2)
			if extender is not None:
				if self.ComputeDistance(extender,p2) < .01:
					#TODO get new path
					# print('shortening path now')
					# print(len(path))
					badIndeces = [p1index+1,p2index]
					# print(len(path[badIndeces[0]:badIndeces[1]]))
					if (badIndeces[1]-badIndeces[0]) != 0:
						path[badIndeces[0]:badIndeces[1]] = []
					else:
						path[badIndeces[0]] = []
					# print len(path)
					path[badIndeces[0]] = p1
					path.insert(badIndeces[0]+1,p2)
					# print('new path created')
					# print(path)

			#TODO repeate until timeout
			current_time = time.time()-start_time
			i = 0
		return path


	def InitializePlot(self, goal_config):
		self.fig = pl.figure()
		lower_limits, upper_limits = self.boundary_limits
		pl.xlim([lower_limits[0], upper_limits[0]])
		pl.ylim([lower_limits[1], upper_limits[1]])
		pl.plot(goal_config[0], goal_config[1], 'gx')

		# Show all obstacles in environment
		for b in self.robot.GetEnv().GetBodies():
			if b.GetName() == self.robot.GetName():
				continue
			bb = b.ComputeAABB()
			pl.plot([bb.pos()[0] - bb.extents()[0],
					 bb.pos()[0] + bb.extents()[0],
					 bb.pos()[0] + bb.extents()[0],
					 bb.pos()[0] - bb.extents()[0],
					 bb.pos()[0] - bb.extents()[0]],
					[bb.pos()[1] - bb.extents()[1],
					 bb.pos()[1] - bb.extents()[1],
					 bb.pos()[1] + bb.extents()[1],
					 bb.pos()[1] + bb.extents()[1],
					 bb.pos()[1] - bb.extents()[1]], 'r')
					
					 
		pl.ion()
		pl.show()
		
	def PlotEdge(self, sconfig, econfig):
		pl.plot([sconfig[0], econfig[0]],
				[sconfig[1], econfig[1]],
				'k.-', linewidth=2.5)
		pl.draw()


