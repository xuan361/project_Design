# project_Design



## main 分支：

主分支，最终的、稳定的、经过测试没有 bug 的、可部署于生产环境的分支。




## dev 分支：

主要开发分支，贯穿于整个项目的生命周期，请将写好的代码上传到该分支。

### Module_CPU各文件说明
**1.编译程序**
将 program.txt 中的代码编译成 machinecode 机器码文件

**2.design**
放的是CPU所需要的设计文件

**3.tb**
CPU在vivado上进行测试代码是否正确的仿真文件

**4.transport**
将字节码从电脑传输到板子的传输文件

**5.XDC**
CPU所需要的约束文件

## Dai_dev 分支：
代子祥负责的开发分支。

## feature 分支：
功能模块开发分支，对应于一个特定的功能模块
该分支以 dev 分支为基线，完成开发工作后再合并到 dev 分支
**命名规则：feature/NAME 或 feature-NAME**