# การใช้ SQLAlchemy กับ MCP Server สำหรับ MSSQL

## การเปลี่ยนแปลงที่ทำ

เราได้ปรับปรุง MCP Server สำหรับ MSSQL เพื่อใช้ SQLAlchemy แทน pymssql โดยตรง ซึ่งช่วยให้การเชื่อมต่อและการทำงานกับฐานข้อมูลมีความยืดหยุ่นและเสถียรมากขึ้น โดยมีการเปลี่ยนแปลงดังนี้:

1. เพิ่ม SQLAlchemy เป็นไลบรารี่ที่จำเป็นใน `requirements.txt` และ `environment.yml`
2. เปลี่ยนจากการเชื่อมต่อโดยตรงด้วย pymssql เป็นใช้ SQLAlchemy engine
3. ปรับเปลี่ยนฟังก์ชันในการดึงข้อมูลให้ใช้ SQLAlchemy
4. สร้างไฟล์ debug ใหม่สำหรับการวิเคราะห์ปัญหาการเชื่อมต่อโดยเฉพาะ

SQLAlchemy ช่วยให้เราทำงานกับฐานข้อมูลในระดับที่สูงขึ้นโดยมีข้อดีคือ:
- การจัดการความสัมพันธ์ของข้อมูลที่ดีขึ้น
- การรองรับหลาย Database engine โดยไม่ต้องเปลี่ยน code มากนัก
- การจัดการ connection pooling ทำให้ประสิทธิภาพดีขึ้น
- มี type checking และความปลอดภัยที่ดีขึ้น

## วิธีการใช้งาน

1. **ติดตั้ง SQLAlchemy**:
   ```bash
   pip install sqlalchemy pymssql
   ```
   หรือเมื่อใช้ conda:
   ```bash
   conda install -c conda-forge sqlalchemy pymssql
   ```

2. **ทดสอบการเชื่อมต่อ**:
   ```bash
   python debug_connection_sqlalchemy.py
   ```

3. **รัน MCP Server**:
   ```bash
   python mssql_server.py
   ```

4. **ตั้งค่า Claude Desktop**:
   ปรับการตั้งค่าใน `claude_desktop_config.json` ให้ชี้ไปที่ Python environment ที่ถูกต้อง:
   ```json
   {
     "mcpServers": {
       "mssql-server": {
         "command": "/path/to/conda/envs/mssql-mcp/bin/python",
         "args": ["/Users/grizzlystudio/Desktop/pythonmssql/mssql_server.py"]
       }
     }
   }
   ```

## การแก้ไขปัญหา

หากคุณยังพบปัญหาในการเชื่อมต่อ ให้ตรวจสอบ:

1. ตรวจสอบการเชื่อมต่อเครือข่าย:
   ```bash
   telnet 35.239.50.206 1433
   ```

2. ตรวจสอบรายละเอียดการแก้ไขปัญหาจากไฟล์ debug:
   ```bash
   python debug_connection_sqlalchemy.py
   ```

3. ตรวจสอบว่าไลบรารี่ที่จำเป็นทั้งหมดถูกติดตั้ง:
   ```bash
   pip list | grep -E 'sqlalchemy|pandas|pymssql|mcp'
   ```

## คำแนะนำเพิ่มเติม

- ใช้ `sqlalchemy` เมื่อต้องการความยืดหยุ่นและการใช้ ORM
- ใช้ `pandas` สำหรับการวิเคราะห์ข้อมูลและการแสดงผล
- ปรับ connection pool size หาก MCP Server จะมีการใช้งานจากหลายผู้ใช้
- อย่าลืมปิด connection หลังการใช้งานเสมอ
