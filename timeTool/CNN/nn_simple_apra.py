import logging

import tensorflow as tf
import numpy as np
from tensorflow.contrib.layers import fully_connected

import argparse

logger = logging.getLogger(__name__)

def simple_preloaded_nn(inputs, labels, keep_prob, alpha, weights):
    # # Probability we dont drop out a neuron
    
    # FC1
    net = fully_connected(
        inputs=inputs, 
        num_outputs=3, 
        weights_initializer=tf.constant_initializer(weights),
        biases_initializer=tf.zeros_initializer(),)

    net = tf.nn.dropout(net, keep_prob)

    # FC2
    net = fully_connected(net, num_outputs=1, activation_fn=None)   

    #Train operations
    with tf.variable_scope("train", reuse=None):
        # RMSE, where net is the outputted predictions
        loss = tf.sqrt(tf.reduce_mean(tf.square(net-labels)))
        # AdamOptimizer is relatively stable and fast as opposed to 
        # GradientDescent
        train_step = tf.train.AdamOptimizer(alpha).minimize(loss)

    return net, loss, train_step

def simple_nn_100(inputs, labels, keep_prob, alpha):
    # # Probability we dont drop out a neuron
    
    # FC1
    net = fully_connected(
        inputs=inputs, 
        num_outputs=100, 
        biases_initializer=tf.zeros_initializer(),
        )

    net = tf.nn.dropout(net, keep_prob)
 
    # FC2
    net = fully_connected(net, num_outputs=1, activation_fn=None)    

    #Train operations
    with tf.variable_scope("train", reuse=None):
        # RMSE, where net is the outputted predictions
        loss = tf.sqrt(tf.reduce_mean(tf.square(net-labels)))        
        # AdamOptimizer is relatively stable and fast as opposed to 
        # GradientDescent
        train_step = tf.train.AdamOptimizer(alpha).minimize(loss)

    return net, loss, train_step

def shuffle_data(inputs, labels, labels_unstandardized):
    # Shuffle data to avoid time dependency in predictions
    len_inputs, len_labels = len(inputs), len(labels)
    if len_inputs != len_labels:
        raise ValueError('Inputs and labels must have the same length. Got '
                         '{0} and {1}'.format(len_inputs, len_labels))
    
    # Shuffle indices in arange(len_inputs) without replacement (i.e. no repeats)
    shuffle_indices = np.random.choice(len_inputs, size=len_inputs, replace=False)

    # Apply ordering to inputs and labels
    shuffle_inputs = inputs[shuffle_indices]
    shuffle_labels = labels[shuffle_indices]
    shuffled_labels_unstandardized = labels_unstandardized[shuffle_indices]
    
    return shuffle_inputs, shuffle_labels, shuffled_labels_unstandardized

def next_batch(inputs, labels, num):
    # Generate next batch, either from shuffled inputs or not shuffled inputs
    if not isinstance(num, int):
        raise ValueError('num must be an int. Got {0}'.format(num))
    len_inputs, len_labels = len(inputs), len(labels)
    if len_inputs != len_labels:
        raise ValueError('Inputs and labels must have the same length. Got '
                         '{0} and {1}'.format(len_inputs, len_labels))

    start = 0
    # Grab the next batch every time the generator is called
    while True:
 	epoch = int(start / len_inputs)
        batch_range = np.arange(start, start+num) % len_inputs
	batch_inputs = inputs[batch_range]
        batch_labels = labels[batch_range]
        yield batch_inputs, batch_labels, epoch
        start += num

def load_data():
    print("Loading files...")

    inputs = np.loadtxt('/reg/d/psdm/XPP/xppl3816/scratch/timeTool_ml/data_source/xppl3816_r51_matrix.dat')

    a,b,all_labels = np.loadtxt('/reg/d/psdm/XPP/xppl3816/scratch/timeTool_ml/data_source/xppl3816_r51_delays.dat', unpack=True)

    weights = np.transpose(np.loadtxt('init_weights.txt').reshape(3,1000))

    # Reshape the labels to appease tf
    all_labels = all_labels.reshape(len(all_labels), 1)
    return inputs, a, b, weights, all_labels

# To be used in ipython to help with parameter entry
def run(auto=True):

    print('---------------------------------------')
    print('Fully connected, 2 layer neural network')
    print('---------------------------------------')
    print

    # Will autofill args with defaults
    if auto:
        alpha 		= 1e-4
        dropout 	= 1.0
        batchsize 	= 100
        epochs 		= 5
        printn 		= 2
        network 	= 3
	shuffle 	= True

    # Command line interface will walk through entry
    elif not auto:

        alpha = 		raw_input('Enter the learning rate, alpha: ') 
	if len(alpha) < 1:	alpha = 1e-4
	else: alpha = 		float(alpha)

        dropout = 		raw_input('Enter the keep probability for dropout: ') 
        if len(dropout) < 1: 	dropout = 1.0
	else: dropout = 	float(dropout)

	batchsize = 		raw_input('Enter the batch size: ')
        if len(batchsize) < 1: 	batchsize = 100
	else: batchsize = 	int(batchsize)

	epochs = 		raw_input('Enter the number of training epochs: ')
	if len(epochs) < 1: 	epochs = 5
	else: epochs = 		int(epochs)
 
        printn = 		raw_input('Enter the number of times loss should be printed in each epoch: ')
	if len(printn) < 1: 	printn = 2
	else: printn = 		int(printn) 
        
	network = 		raw_input('Enter the number of neurons desired in hidden layer. Note only 3 or 100 supported: ')
	if len(network) < 1:	network = 3
	else:			network = int(network)

        shuffle = 		raw_input('Would you like the data shuffled? (Y/N) ')
	if shuffle.lower()=='n':shuffle = False
	else:			shuffle = True

    print('Running network with the following parameters:')
    print(' alpha           = {0}'.format(alpha))
    print(' dropout         = {0}'.format(dropout))
    print(' batchsize       = {0}'.format(batchsize))
    print(' epochs          = {0}'.format(epochs))
    print(' printn          = {0}'.format(printn))
    print(' network         = {0}'.format(network))
    print(' shuffle         = {0}'.format(shuffle))
    print

    # Check if user has already loaded data. If not, make sure main() loads data
    r = raw_input('Has the data been pre-loaded? (Y/N): ')
    if r.lower() == 'n':
        initialize_data_variables()

    main(alpha, dropout, batchsize, epochs, printn, network, shuffle, False)

def initialize_data_variables():

    global global_inputs, global_loaded_weights, global_labels
    global_inputs, a, b, global_loaded_weights, global_labels = load_data()

def main(alpha_arg, dropout_arg, batchsize_arg, epochs_arg, printn_arg, network_arg, shuffle_arg, read_data):

    # If run from main method (not ipython), load data
    if read_data:
	initialize_data_variables()
   
    # Create a standardized set of labels
    all_labels_standardized = (global_labels-global_labels.mean()) / global_labels.std()

    logging.info("Defining placeholder variables")

    # Define the variables
    with tf.variable_scope('input'):
        lineouts = tf.placeholder(tf.float32, shape=[None, 1000])
        labels = tf.placeholder(tf.float32, shape=[None, 1])
        keep_prob = tf.placeholder(tf.float32)
        alpha = tf.placeholder(tf.float32)

    print("Defining networks")
    if(network_arg == 3):
        # Weights pre-initialized
        inp_net, inp_loss, inp_train_step = simple_preloaded_nn(
            lineouts, labels, keep_prob, alpha, global_loaded_weights)
    elif(network_arg==100):
        # Weights set randomly
        inp_net, inp_loss, inp_train_step = simple_nn_100(
            lineouts, labels, keep_prob, alpha)
    
    # Begin the session
    with tf.Session() as sess:
        print("Beginning session")
        sess.run(tf.global_variables_initializer())

        if shuffle_arg:    
            final_inputs, final_labels, final_labels_unstandardized = shuffle_data(global_inputs, all_labels_standardized, global_labels)
        else:
 	    final_inputs, final_labels, final_labels_unstandardized = global_inputs, all_labels_standardized, global_labels 

        # Set the run Parameters
        batch_generator = next_batch(final_inputs, final_labels, 
                                     batchsize_arg)

        print("Running for {0} epochs, using a batch size of {1}, "
                    "printing {2} times per epoch".format(
                        epochs_arg, batchsize_arg, printn_arg))        
        
        epoch, i = 0, 0
	while epoch < epochs_arg:

            # Fetch next batch of size batchsize_arg
            batch = next(batch_generator)
	    
	    # Track what epoch and if just changed epochs (for printing purposes)
	    if (batch[2] - epoch) > 0: 	i = 0
  	    epoch = batch[2]

            # Every step run training!
            _, iter_loss, output = sess.run(
                [inp_train_step, inp_loss, inp_net], 
                feed_dict={lineouts: batch[0], labels: batch[1], keep_prob: dropout_arg, alpha: alpha_arg})

            # Print the loss printn times
            if not i % (((len(global_labels) / batchsize_arg) + 1) // printn_arg):
                print("Epoch {0}	Iteration {1}	Loss of {2}".format(
                    epoch, i, iter_loss))
	    i += 1        

        # Check if converged to case where all values are the same
        if output.mean() == 0. and output.std() == 0.:
            print('Converged incorrectly. Last batch output = {0}'.format(output))

        # Test the network on the same data (for now)
        ret = sess.run(
            [inp_net],
            feed_dict={lineouts: final_inputs, labels: final_labels, keep_prob: 1.0, alpha: alpha_arg}) 

	# Print unstandardized RMSE
        rmse = np.sqrt(np.mean((((np.multiply(ret,global_labels.std()))+global_labels.mean())-final_labels_unstandardized)**2))
        print("Got an RMSE (unstandardized) of {0}".format(rmse))	
    
if __name__ == "__main__":

    # Set up arg parser 
    helpstr = 'Fully connected, 2 layer neural network'
    parser = argparse.ArgumentParser(description=helpstr);
    parser.add_argument('-a','--alpha', dest='alpha', type=float, help='learning rate', default=1e-4)
    parser.add_argument('-d','--dropout', dest='dropout', type=float, help='keep probability for dropout', default=1.0)
    parser.add_argument('-b','--batchsize', dest='batchsize', type=int, help='batch size', default=100)
    parser.add_argument('-e','--epochs', dest='epochs', type=int, help='num training epochs', default=5)
    parser.add_argument('-p','--printn', dest='printn', type=int, help='print loss n times in each epoch', default=2)
    parser.add_argument('-n','--network', dest='network', type=int, help='number of neurons in hidden layer', default=3)
    parser.add_argument('-s','--shuffle', dest='shuffle', type=bool, help='whether or not to shuffle the data', default=True)

    args = parser.parse_args()

    if not (args.network == 3 or args.network == 100):
        print('{0} neurons in hidden layer not supported'.format(args.network))

    args = parser.parse_args();

    main(args.alpha, args.dropout, args.batchsize, args.epochs, args.printn, args.network, args.shuffle, True)
