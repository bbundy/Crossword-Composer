#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
from xword.models import  Clue, Answer
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import gc

def queryset_iterator(queryset, chunksize=1000):
    '''''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in its
    memory at the same time while django normally would load all rows in its
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()

count = 0
q = Clue.objects.only("answer")
for cl in queryset_iterator(q.all()): 
    try:
        ans = Answer.objects.get(answer=cl.answer)
        ans.count += 1
        ans.save()

    except ObjectDoesNotExist:
        ans = Answer(answer=cl.answer, count=1)
        ans.save()
    except MultipleObjectsReturned:
        print "multiple clues found for %s" % ans.answer
    count += 1
    if count % 10000 == 0:
        print count
