
# Define the replica set name
REPL_SET="mongo-replica-set"

# Wait for the MongoDB servers to be ready
sleep 10

# Initialize the replica set
mongosh --host mongo1 --eval "rs.initiate({
  _id: '$REPL_SET',
  members: [
    { _id: 0, host: 'mongo1:27017' },
    { _id: 1, host: 'mongo2:27017' },
    { _id: 2, host: 'mongo3:27017' }
  ]
})"