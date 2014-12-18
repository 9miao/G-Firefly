####G-Firefly简介+Firefly-Gevent重要迭代版本alpha 0.1.5介绍
在alpha 0.1.5做了如下的改进：
１、单node节点断开与root节点的连接后自动重连。
２、修改了gfirefly的底层库gtiwsted,将socket发送数据放到一个协程中进处理，解决了

    AssertionError: This socket is already used by another greenlet

的错误

gtwisted的开源地址:https://github.com/9miao/gtwisted

####G-Firefly简介+Firefly-Gevent重要迭代版本alpha 0.1.2介绍


firefly-gevent 是firefly的gevent版本。相比现在的firefly版本使用的twisted，gevent更加的精简。<br/>

gevent就是一个基于coroutine的python网络开发框架。协程是一种并发模型，但不同于thread和callback，它的所有task都是可以在一个线程里面执行，然后可以通过在一个task里面主动放弃执行来切换到另一个task执行，它的调度是程序级的，不像thread是系统级的调度。<br/>

Gevent最明显的特征就是它惊人的性能，尤其是当与传统线程解决方案对比的时候。在这一点上，当负载超过一定程度的时候，异步I/O的性能会大大的优于基于独立线程的同步I/O这几乎是常识了。同时Gevent提供了看上去非常像传统的基于线程模型编程的接口，但是在隐藏在下面做的是异步I/O。更妙的是，它使得这一切透明。（此处意思是你可以不用关心其如何实现，Gevent会自动帮你转换）<br/>

忽略其他因素，Gevent性能是线程方案的4倍左右（在这个测试中对比的是Paste，译者注：这是Python另一个基于线程的网络库）
与单进程多线程模型相比，多进程和协程是更加Scalable的模型。在高并发场景下，采用多进程模型编制的程序更加容易Scale Out，而协程模型可以使单机的并发性能大幅提升，达到Scale Up的目的。所以，未来服务器端并发模型的标配估计会是：每个核一个进程，每个进程是用协程实现的微线程。<br/>

在编码方面，多线程模型带来的共享资源加解锁的问题一直是程序员的梦魇。而用多进程模型编程时，会自然鼓励程序员写出避免共享资源的程序，从而提高扩展性。而Python目前的协程实现都为非抢占式调度，程序员自行控制协程切换时机，因此也可以避免绝大多数令人头疼的加解锁问题。这些都利于写出更稳定的代码。<br/>

另外，和同样具有很好并发性能的事件驱动模型相比，用协程实现的微线程，在逻辑表达上非常友好和直白，无须在不知道什么时候会发生的event和一层套一层的callback中纠结和扭曲（正如Twisted其名）。对于写过多线程程序的程序员而言，协程带来的微线程模型几乎可以实现无痛提高并发性能。<br/>

firefly-gevent结合了gevent的性能，封装了网络IO处理、数据库IO读写缓存、分布式进程间接口调用。这样使得游戏服务端的开发变得更加的轻松简单，开发者不必在面对这些的技术难题，专心致力于游戏玩法逻辑的开发。<br/>




####Firefly-gevent Alpha 0.1.2 Release – an Important Version Update


Firefly-gevent is firefly gevent version which is more of simplicity comparing to current Firefly twisted version.<br/>

Based on coroutine, python-written gevent is a web development framework. Coroutine is a concurrency model, but unlike to thread and callback, all its tasks can be executed in a single thread, and are able to swap to another task for execution by initial aborting in a task. It has program-level schedule rather than thread’s system-level schedule.<br/>

Amazing performance is Gevent’s most obvious feature, especially when you compare it to traditional thread solution. On this point, an almost common sense fact is that asynchronous I/O performance will be significantly superior to separate thread-based synchronous I/O when load is over a certain degree. In the meantime, Gevent provides seemingly much alike traditional port that was programmed based on thread model. However this port’s real identity is asynchronous I/O, and what’s more wonderful part is that it makes all these transparent (here it means you don't need to worry about how it function itself, Gevent will help you finish the switching job).<br/>

Ignoring other factors, Gevent performance is four times greater than thread solution (here in this test we use Paste as contrast, note: Paste is another thread-based web library of Python). Comparing to single process multi thread model, multi process and coroutine is more scalable model. In high concurrency situation, multi process model compiled program is easier to Scale Out, and coroutine model could significantly improve single host concurrency performance to achieve Scale Up. So the standardized configuration of future server concurrency model probably is: each core contains a process which is actually a micro thread that realized by coroutine.<br/>

Coding-wise, shared resources lock and unlock problem caused by multi thread model has been a nightmare to programmer since ever. But when you code with multi process model, its philosophy will inspire programmers write programs that has avoiding shared resources feature which will consequently improve system robustness. And currently all Python coroutine realization are non preemptive schedule, it enables programmers themselves to control multi program switch timing so as to avoid a majority of worrisome lock and unlock problems. All these are advantageous for programmers to write more established codes.<br/>

In addition, comparing to event-driven model that also has great concurrency performance, coroutine realized micro thread has very friendly and straight forward logic expression and allows programmers to free from struggling and twisting in unpredictable event and multi-layer covered callback (what Twisted implicates…). Micro thread model of coroutine could help multi thread programs writer to almost realize a painless concurrency performance upgrade.<br/>

Firefly-gevent, with gevent performance, encapsulates network IO processing, database IO read and write cache, interface calls among distributed processes, which 
allows game server side development become more easy and simple, and developers focus on gameplay logic development with no burden on technical problems.<br/>


