### 简介

对象池中管理的对象，可以是网络连接，也可以是其它任意对象。在这里，对象被分为两大类：

* 可以被多线程共享的对象，比如线程安全的连接对象。这些对象应该使用 SharedObjectPool 来管理

* 线程独享的对象，比如非线程安全的连接对象。这些对象应该使用 DedicateObjectPool 来管理

线程从对象池中获取对象的过程大致如下：

1. 查看是否有可用对象（比如，未被使用的对象、未达到最大共享次数的对象），如有，返回其中一个可用对象
2. 对象池是否满了，如果未满，创建新一个对象，将其放入对象池，并返回该对象
3. 线程等待到超时（超时时间由 `timeout` 参数设置）或者被唤醒（当其他线程释放或销毁对象时，会唤醒所有正在等待的线程）
4. 重复步骤 1 到 3，直到获取到对象或达到最大尝试次数
