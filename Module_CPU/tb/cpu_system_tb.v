// cpu_system_tb.v
`timescale 1ns / 1ps
module cpu_system_tb();
    // Testbench信号
    reg CLK;
    reg RESET; // 模拟物理按键
    reg uart_rx_pin;   // 模拟串口输入
    reg wait_transport;

    wire led1; // 连接到顶层模块的LED输出
    wire led2; // 连接到顶层模块的LED输出
    wire led3; // 连接到顶层模块的LED输出
    wire led4; // 连接到顶层模块的LED输出

    wire  dig1;    //数码管从左到右为1-6
    wire  dig2;
    wire  dig3;
    wire  dig4; 
    wire  dig5; 
    wire  dig6; 
    wire [6:0] out; 

    localparam MAX_INSTRUCTIONS = 256; // Testbench内存能存储的最大指令数

    // 实例化顶层模块
    SingleCPU uut (
        .CLK(CLK),
        .RESET(RESET),
        .wait_transport(wait_transport),
        .uart_rx_pin(uart_rx_pin),
        .led1(led1),
        .led2(led2),
        .led3(led3),
        .led4(led4),

        .dig1(dig1),
        .dig2(dig2),
        .dig3(dig3),
        .dig4(dig4),
        .dig5(dig5),
        .dig6(dig6),
        .out(out)
    );


    // 时钟生成
    localparam CLK_PERIOD = 20; // 50MHz 时钟周期
    always #(CLK_PERIOD/2) CLK = ~CLK;

    // UART 发送任务 (与之前相同)
    task send_uart_byte;
        input [7:0] byte_to_send;
        integer i;
    begin
        uart_rx_pin = 1'b0; // Start bit
        #(CLK_PERIOD * 5208);

        for (i = 0; i < 8; i = i + 1) begin // Data bits (LSB first)
            uart_rx_pin = byte_to_send[i];
            #(CLK_PERIOD * 5208);
        end

        uart_rx_pin = 1'b1; // Stop bit
        #(CLK_PERIOD * 5208);
        #(CLK_PERIOD * 5); // Short delay after byte
    end
    endtask

    task send_uart_word;
        input [15:0] word_to_send;
        reg [7:0] lsb;
        reg [7:0] msb;
    begin
        lsb = word_to_send[7:0];
        msb = word_to_send[15:8];

        // $display("[%0t ns] TB: Sending LSB: 0x%h, MSB: 0x%h for Word: 0x%h", $time, lsb, msb, word_to_send);
        send_uart_byte(lsb);
        send_uart_byte(msb);
        #(CLK_PERIOD * 10); // Delay after word
    end
    endtask
    

    // 主仿真序列
    initial begin : INIT_BLOCK
        // Testbench内部存储指令的内存和参数
        reg [15:0] tb_instruction_memory [0:MAX_INSTRUCTIONS-1];
        integer num_instructions_read;
        integer file_handle;
        integer read_status;
        reg [15:0] temp_instr_word;
        integer i; // 如果循环中使用，也在此声明

        
        // 1. 初始化
        CLK = 0;
        RESET = 1;
        wait_transport = 1;
        uart_rx_pin = 1'b0; // UART idle high
        num_instructions_read = 0;

        #20; RESET <= 1'b0; 
        #20; RESET <= 1'b1; 
        #20; wait_transport <= 1'b0; 
        #20; wait_transport <= 1'b1; 

        $display("SIMULATION START: Initializing...");
        #(CLK_PERIOD * 50);

        // 2. 从文件读取指令到Testbench内存

        file_handle = $fopen("D:/learn/Git/testgit/Module_CPU/transport/machineCode.txt", "r");
        if (file_handle == 0) begin
            $display("TB ERROR:The 'machineCode.txt' file cannot be opened. Please confirm that the file exists and each line contains a 16-bit binary number.");
            $finish;
        end

        $display("TB: Reading instructions from machineCode.txt...");
        while (!$feof(file_handle) && num_instructions_read < MAX_INSTRUCTIONS) begin
            read_status = $fscanf(file_handle, "%b\n", temp_instr_word); // 读取一个16位二进制数
            if (read_status == 1) begin     // $fscanf成功读取1项
                tb_instruction_memory[num_instructions_read] = temp_instr_word;
                num_instructions_read = num_instructions_read + 1;
            end else if (!$feof(file_handle)) begin
                 // 如果不是文件末尾但读取失败，可能是格式问题
                $display("TB WARNING: Invalid format or empty line in machineCode.txt. Skipping.");
                 // 为了简单起见，这里我们假设fscanf能处理或跳过（如果它遇到非二进制行，read_status可能不为1）
                 // 更健壮的解析需要 $fgets 和字符串处理
            end
        end
        $fclose(file_handle);
        $display("TB: Finished reading. Total instructions read: %0d", num_instructions_read);

        if (num_instructions_read == 0 && !$test$plusargs("ALLOW_EMPTY_PROGRAM")) begin
             $display("TB WARNING: No instructions read from machineCode.txt. Sending count 0.");
        end
        
        #(CLK_PERIOD * 50);
        $display("[%0t ns] TB: System initialized. LED should be ON (paused). Current LED: %b", $time, led4);

        // 3. 发送指令总数
        $display("[%0t ns] TB: Sending instruction count (%0d)...", $time, num_instructions_read);
        send_uart_word(num_instructions_read[15:0]); // 发送读取到的数量

        // 4. 逐条发送机器码
        if (num_instructions_read > 0) begin
            $display("[%0t ns] TB: Sending %0d instructions...", $time, num_instructions_read);
            for (i = 0; i < num_instructions_read; i = i + 1) begin
                $display("[%0t ns] TB: Sending Instruction %0d (0x%h)...", $time, i, tb_instruction_memory[i]);
                send_uart_word(tb_instruction_memory[i]);
            end
        end

        $display("[%0t ns] TB: All instructions have been sent. At this point, the LED should be in the off state. Current status of the indicator light: %b", $time, led4);
        #(CLK_PERIOD * 100); // 等待一段时间观察LED状态是否已熄灭

        // 5. 模拟按下复位/启动按钮
        $display("[%0t ns] TB: Press the 'RESET' button to start the CPU...", $time);
        RESET = 0;
        #(CLK_PERIOD * 5);
        RESET = 1;
        $display("[%0t ns] TB: The reset operation has been completed. The CPU should have started running. The current status of the indicator lights: %b", $time, led4);

        // 6. 允许CPU运行一段时间
        $display("[%0t ns] TB: CPU is running...", $time);
        #(CLK_PERIOD * num_instructions_read * 10000); // 根据指令数量和复杂性调整运行时间

        $display("[%0t ns] TB: The CPU has completed its operation. The final LED status is: %b", $time, led4);

        // 7. 结束仿真
        $display("仿真结束");
        $finish;
    end

endmodule


