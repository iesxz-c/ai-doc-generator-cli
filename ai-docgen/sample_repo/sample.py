class Solution(object):
    def twoSum(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """
        d={}
        for i,j in enumerate(nums):
            k=target-j
            if k in d:
                return [d[k],i]
            else:
                d[j]=i

