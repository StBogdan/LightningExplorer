from django.db import models

# Create your models here.
class Metric(models.Model):

    title           = models.CharField(max_length=50)
    description     = models.CharField(max_length=250)
    dataset_type    = models.CharField(max_length=100, default= "'scatter'")
    dataset_labels  = models.CharField(max_length=999, blank=True) # Optional, expect to find in "<dataset_file>_labels"
    dataset_options = models.CharField(max_length=999, blank=True) #Might be a bit too much
    dataset_url  = models.CharField(max_length=250) #Path to file containing the dataset
    image_url    = models.CharField(max_length=50)
    parent       = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    network    = models.CharField(max_length=8)
    index_together = ["pub_date", "deadline"]

class Node(models.Model):
    date_logged = models.DateTimeField(db_index=True)    # Time logged
    network     = models.CharField(max_length=8)
    last_update = models.IntegerField()     # Last_update (Unix timestamp)

    pub_key = models.CharField(max_length=67)     # PubKey
    alias   = models.CharField(max_length=100)    # Alias

    # Color
    color    = models.CharField(max_length=20)
    # Computed_num_chan
    channels = models.IntegerField()
    # Computed_total_capacity
    capacity = models.BigIntegerField()
    class Meta: #For Primary key with 2 fields
        unique_together = (('date_logged', 'pub_key'),)

# [{'addr': '127.0.0.1:9735', 'network': 'tcp'}]
class Address(models.Model):
    date_logged = models.DateTimeField(db_index=True)    # Time logged
    node        = models.ForeignKey('Node', on_delete=models.CASCADE)
    date_logged = models.DateTimeField()    # Time logged
    addr    = models.CharField(max_length=100) #May be IPv6
    network = models.CharField(max_length=5)


class Channel(models.Model):
    date_logged = models.DateTimeField(db_index=True)    # Time logged
    network     = models.CharField(max_length=8)
    chan_id     = models.CharField(max_length=20) #id
    #Last_update
    last_update = models.IntegerField()     # Last_update (Unix timestamp)

    node1_pub =  models.ForeignKey('Node', null=True, on_delete=models.SET_NULL, related_name='node1_pub')
    node2_pub =  models.ForeignKey('Node', null=True, on_delete=models.SET_NULL, related_name='node2_pub')
    #Capacity
    capacity   = models.BigIntegerField()
    chan_point = models.CharField(max_length=67)
    # Example of chan point
    # d3dcc7be9d8aa5524cd57a8689aca0bf91ad838300e58eeeb19a5b7dd884f10e:1
    class Meta: #For Primary key with 2 fields
        unique_together = (('date_logged', 'chan_id'),)


# "node1_policy": {
#     "time_lock_delta": 144,
#     "min_htlc": "1000",
#     "fee_base_msat": "1000",
#     "fee_rate_milli_msat": "1"
# }
class Node_Policy(models.Model):
    date_logged = models.DateTimeField()    # Time logged
    network      = models.CharField(max_length=8)
    channel     = models.ForeignKey('Channel', on_delete=models.CASCADE)
    node        = models.ForeignKey('Node', on_delete=models.CASCADE)
    time_lock_delta     = models.BigIntegerField() #time_lock_delta
    min_htlc            = models.BigIntegerField() #min_htlc
    fee_base_msat       = models.BigIntegerField() #fee_base_msat #Because values of 2^32-1 appear on mainnet policies
    fee_rate_milli_msat = models.BigIntegerField() #fee_rate_milli_msat
