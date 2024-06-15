#!/bin/bash

# Define the replica set name
REPL_SET="myReplicaSet"

# Initialize the replica set
mongo --host mongo1 --eval "rs.initiate({_id: '$REPL_SET', members: [{_id: 0, host: 'mongo1:27017'}, {_id: 1, host: 'mongo2:27017'}, {_id: 2, host: 'mongo3:27017'}]})"
