import operator
from collections import defaultdict
from pprint import pprint
from dataclasses import dataclass


class TreeNode:
    def __init__(self, name: str, count: int, parent):
        self.name = name
        self.count = count
        self.parent = parent
        self.nodeLink = None
        self.childs = {}

    def inc(self, num: int):
        self.count += num

    def disp(self, ind=1):
        print("    " * ind, self.name, self.count)
        for child in self.childs.values():
            child.disp(ind=ind + 1)


@dataclass
class HeaderTableItem:
    count: int
    node: TreeNode


def createTree(dataSet: dict(), minSup=1):
    headerTable = {}

    # 遍历，统计各项集出现的次数
    for key in dataSet.keys():
        for item in key:
            if item in headerTable:
                headerTable[item].count += 1
            else:
                headerTable[item] = HeaderTableItem(count=1, node=None)

    # 遍历各元素，删除不满足最小支持度的元素
    headerTable = {x: headerTable[x] for x in headerTable if headerTable[x].count > minSup}
    freqItemSet = set(headerTable.keys())

    # 叵没有元素满足最小支持度要求，返回None，结束函数
    if len(freqItemSet) == 0:
        return None, None

    # 开始构建树
    retTree = TreeNode(name="Null Set", count=1, parent=None)

    for tranSet, count in dataSet.items():
        localD = {}
        orderedItems = sorted([x for x in tranSet if x in headerTable], key=lambda x: -1 * headerTable[x].count)
        pprint(orderedItems)

        if orderedItems:
            updateTree(orderedItems, retTree, headerTable, count)

    return retTree, headerTable


# 树的更新函数
# items为按出现次数排序后的项集，是待更新到树中的项集；count为items项集在数据集中的出现次数
# inTree为待被更新的树；headTable为头指针表，存放满足最小支持度要求的所有元素
def updateTree(items, inTree, headerTable, count):
    item = items.pop(0)

    # 若项集items当前最频繁的元素在已有树的子节点中，则直接增加树子节点的计数值，增加值为items[0]的出现次数
    if item in inTree.childs:
        inTree.childs[item].inc(count)

    else:  # 若项集items当前最频繁的元素不在已有树的子节点中（即，树分支不存在），则通过treeNode类新增一个子节点
        inTree.childs[item] = TreeNode(name=item, count=count, parent=inTree)

        # 若新增节点后表头表中没有此元素，则将该新增节点作为表头元素加入表头表
        if headerTable[item].node == None:
            headerTable[item].node = inTree.childs[item]
        else:  # 若新增节点后表头表中有此元素，则更新该元素的链表，即，在该元素链表末尾增加该元素
            updateHeader(headerTable[item].node, inTree.childs[item])

    # 对于项集items元素个数多于1的情况，对剩下的元素迭代updateTree
    if len(items) > 0:
        updateTree(items, inTree.childs[item], headerTable, count)


# 元素链表更新函数
# nodeToTest为待被更新的元素链表的头部
# targetNode为待加入到元素链表的元素节点
def updateHeader(nodeToTest, targetNode):
    # 若待被更新的元素链表当前元素的下一个元素不为空，则一直迭代寻找该元素链表的末位元素
    while nodeToTest.nodeLink != None:
        nodeToTest = nodeToTest.nodeLink  # 类似撸绳子，从首位一个一个逐渐撸到末位
    # 找到该元素链表的末尾元素后，在此元素后追加targetNode为该元素链表的新末尾元素
    nodeToTest.nodeLink = targetNode


# 加载简单数据集
def loadSimpDat():
    simpDat = [['r', 'z', 'h', 'j', 'p'],
               ['z', 'y', 'x', 'w', 'v', 'u', 't', 's'],
               ['z'],
               ['r', 'x', 'n', 'o', 's'],
               ['y', 'r', 'x', 'z', 'q', 't', 'p'],
               ['y', 'z', 'x', 'e', 'q', 's', 't', 'm']]
    return simpDat


# 将列表格式的数据集转化为字典格式
def createInitSet(dataSet):
    retDict = {}
    for trans in dataSet:
        retDict[frozenset(trans)] = 1
    return retDict


# 由叶节点回溯该叶节点所在的整条路径
# leafNode为叶节点，treeNode格式；prefixPath为该叶节点的前缀路径集合，列表格式，在调用该函数前注意prefixPath的已有内容
def ascendTree(leafNode, prefixPath):
    if leafNode.parent != None:
        prefixPath.append(leafNode.name)
        ascendTree(leafNode.parent, prefixPath)


# 获得指定元素的条件模式基
# basePat为指定元素；treeNode为指定元素链表的第一个元素节点，如指定"r"元素，则treeNode为r元素链表的第一个r节点
def findPrefixPath(basePat, treeNode):
    condPats = {}  # 存放指定元素的条件模式基
    while treeNode != None:  # 当元素链表指向的节点不为空时（即，尚未遍历完指定元素的链表时）
        prefixPath = []
        ascendTree(treeNode, prefixPath)  # 回溯该元素当前节点的前缀路径
        if len(prefixPath) > 1:
             condPats[frozenset(prefixPath[1:])] = treeNode.count  # 构造该元素当前节点的条件模式基
        treeNode = treeNode.nodeLink  # 指向该元素链表的下一个元素
    return condPats


# 有FP树挖掘频繁项集
# inTree: 构建好的整个数据集的FP树
# headerTable: FP树的头指针表
# minSup: 最小支持度，用于构建条件FP树
# preFix: 新增频繁项集的缓存表，set([])格式
# freqItemList: 频繁项集集合，list格式

def mineTree(inTree, headerTable, minSup, preFix, freqItemList):
    # 按头指针表中元素出现次数升序排序，即，从头指针表底端开始寻找频繁项集
    #bigL = [v[0] for v in sorted(headerTable.items(), key=lambda p: p[1].count)]
    bigL = sorted([x for x in headerTable], key=lambda x: headerTable[x].count)

    for basePat in bigL:
        # 将当前深度的频繁项追加到已有频繁项集中，然后将此频繁项集追加到频繁项集列表中
        newFreqSet = preFix.copy()
        newFreqSet.add(basePat)
        print("freqItemList add newFreqSet", newFreqSet)
        freqItemList.append(newFreqSet)
        # 获取当前频繁项的条件模式基
        condPatBases = findPrefixPath(basePat, headerTable[basePat].node)
        # 利用当前频繁项的条件模式基构建条件FP树
        myCondTree, myHead = createTree(condPatBases, minSup)
        # 迭代，直到当前频繁项的条件FP树为空
        if myHead != None:
            mineTree(myCondTree, myHead, minSup, newFreqSet, freqItemList)


simpDat = loadSimpDat()
dataSet = createInitSet(simpDat)
pprint(dataSet)
myFPtree1, myHeaderTab1 = createTree(dataSet, minSup=3)
myFPtree1.disp(), myHeaderTab1
freqItems = []
mineTree(myFPtree1, myHeaderTab1, 3, set([]), freqItems)
pprint(freqItems)
