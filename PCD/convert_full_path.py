def convert_comma_to_space(input_file, output_file):
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                # 替换逗号为单个空格
                converted_line = line.replace(',', ' ')
                outfile.write(converted_line)
        print(f"转换完成，结果已保存到: {output_file}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    input_file = "/media/airs/E/PROJECTS/ws_livox/src/FAST_LIO/PCD/full_path.txt"
    output_file = "/media/airs/E/PROJECTS/ws_livox/src/FAST_LIO/PCD/full_path_space.txt"
    convert_comma_to_space(input_file, output_file)