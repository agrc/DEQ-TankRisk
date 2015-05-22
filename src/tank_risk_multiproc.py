'''
Created on May 8, 2015

@author: kwalker
'''
import multiprocessing, logging, sys
import time, configs, arcpy, os

class Consumer(multiprocessing.Process):
    
    def __init__(self, task_queue, result_queue, outputGdb):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.outputGdb = outputGdb#os.path.join(outputDir, ) 

    def run(self):
        proc_name = self.name
        print proc_name
        sys.stdout.flush()
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                #print '%s: Exiting' % proc_name
                self.task_queue.task_done()
                break
            
#             f = open(str(next_task) + ".txt", "r")
#             f.close()
            try:
                #print '%s: %s %f' % (proc_name, next_task, time.time())
                taskStartTime = time.time()
                answer = next_task.createNearTable(self.outputGdb)
                answer += " time: {}".format(time.time() - taskStartTime)
                self.task_queue.task_done()
                self.result_queue.put(answer)
            except Exception as e:
                print e
                sys.stdout.flush()
        return


class Task(object):
    def __init__(self, tankPoints, riskFeature):
        self.tanks = tankPoints
        self.risk = riskFeature
        
    def __call__(self):
        time.sleep(0.1) # pretend to take some time to do the work
        return '%s  %s' % (self.tanks, self.risk)
        
    def createNearTable(self, outputGdb):
        inFeature = self.tanks
        nearTablePrefix = "near_"
        nearTime = time.time()
        nearTableSuffix = self.risk.split(".")[-1]
        nearTable = os.path.join(outputGdb, nearTablePrefix + nearTableSuffix)
        nearFeature = os.path.join(self.risk)
        arcpy.GenerateNearTable_analysis (inFeature, nearFeature, nearTable)
        #print "Near_{}: {}".format(nearTableSuffix, time.time() - nearTime)
        return nearTable
    
    def __str__(self):
        return 'check_%s_%s' % (self.tanks, self.risk)
    



# def _getGeodcodedAddresses(apiKey, inputTable, tempDir, num):
#     inputTable = inputTable
#     idField = "IDNUM"
#     addressField = "STREET"
#     zoneField = "ZONE"
#     locator = "Address points and road centerlines (default)"
#     spatialRef = "NAD 1983 UTM Zone 12N"
#     outputDir = tempDir
#     addrResultTable =  "ResultsFromGeocode_" + str(num)  + ".csv"
#         
# 
#     import GeocodeAddressTable
#     Tool = GeocodeAddressTable.TableGeocoder(apiKey, inputTable, idField, addressField, zoneField, locator, spatialRef, outputDir, addrResultTable)
#     Tool.start()
# 
#     return addrResultTable


if __name__ == '__main__':
    
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.DEBUG)
    
    tankPoints = r"Database Connections\agrc@SGID10@gdb10.agrc.utah.gov.sde\SGID10.ENVIRONMENT.FACILITYUST" 
    riskFeatures = configs.MapSource().getSelectedlayers()
    print riskFeatures
    outputDirectory = os.path.join(r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\DEQ-TankRisk\data\outputs",
                                   "outGdbs" + time.strftime("%Y%m%d%H%M%S"))
    os.makedirs(outputDirectory)
   
    # Establish communication queues
    tasks = multiprocessing.JoinableQueue()
    results = multiprocessing.Queue()

    
    # Start consumers
    consumers = []
    num_consumers = multiprocessing.cpu_count() * 2
    print 'Creating %d consumers' % num_consumers
    gdbCreateTime = time.time()#timing
    for i in xrange(num_consumers):
        processGdb = os.path.join(outputDirectory, "nears_" + str(i) + ".gdb")
        arcpy.CreateFileGDB_management(outputDirectory, "nears_" + str(i))
        consumers.append(Consumer(tasks, results, processGdb))
    print "GDB create time: {}".format(time.time() - gdbCreateTime)#timing
       
    consumerStartTime = time.time()#timing
    for w in consumers:
        w.start()
    print "Consumer Start Time: {}".format(time.time() - consumerStartTime)#timing    
        
    # Enqueue jobs
    joinStartTime = time.time()#timing
    num_jobs = len(riskFeatures)
    for risk in riskFeatures:
        #_getGeodcodedAddresses(apiKey, tables[i], outputDirectory, i + 1)
        #print " geocode time: %f" % time.time()
        tasks.put(Task(tankPoints, risk))
    
    # Add a poison pill for each consumer
    for i in xrange(num_consumers):
        tasks.put(None)

    # Wait for all of the tasks to finish
    tasks.join()
    print "Task join time: {}".format(time.time() - joinStartTime)#timing 
    
    # Start printing results
    while num_jobs:
        result = results.get()
        print 'Result:', result
        num_jobs -= 1