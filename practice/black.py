class problems:
 def __init__(self,arr):
    self.arr = arr
arr1=problems([1,2,3,4,5])

 def reverse_list(self,arr):
    arr.reverse()
    return arr
 def count_evens(arr):
    co=0
    for i in arr:
        if i%2==0:
            co+=1
    return co


 def find_max(arr):
    max_value=arr[0]
    for i in range(len(arr)):
        if arr[i]>max_value:
            max_value=arr[i]
    return max_value


arr1.reverse_list()
arr1.count_even()
arr1.find_max()



