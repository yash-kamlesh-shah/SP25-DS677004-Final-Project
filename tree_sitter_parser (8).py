from tree_sitter import Language, Parser

# Load C# language (must match what you compiled in Colab)
LANGUAGE = Language('build/cs-lang.so', 'c_sharp')

# Tree-sitter query for C# methods and constructors
QUERY = LANGUAGE.query("""
(method_declaration) @method
(constructor_declaration) @method
""")

# Shared parser instance
global_parser = Parser()
global_parser.set_language(LANGUAGE)

def node_to_string(src: bytes, node):
    return src[node.start_byte:node.end_byte].decode("utf8")

def make_parser():
    _parser = Parser()
    _parser.set_language(LANGUAGE)
    return _parser

def get_fns_with_doc_comments(src: bytes, tree):
    """
    Extract methods or constructors with leading '///' XML doc comments.
    Returns a list of full source code snippets (comment + method).
    """
    src_lines = src.decode("utf8").split("\n")
    results = []

    for node, kind in QUERY.captures(tree.root_node):
        if kind != "method":
            continue

        method_code = node_to_string(src, node)
        start_line = node.start_point[0]

        # Scan upwards for consecutive '///' lines
        doc_lines = []
        i = start_line - 1
        while i >= 0:
            line = src_lines[i].strip()
            if line.startswith("///"):
                doc_lines.insert(0, line)
                i -= 1
            elif line.startswith("["):  # attributes like [Obsolete]
                i -= 1
            elif line == "":
                i -= 1
            else:
                break

        if doc_lines:
            full = "\n".join(doc_lines + [method_code])
            results.append(full)

    return results

# Additional: detect whether a method returns a value
RETURN_QUERY = LANGUAGE.query("""
(return_statement) @return
""")

def does_have_return(src: str) -> bool:
    """
    Returns True if the given C# source string contains a return statement with a value.
    """
    tree = global_parser.parse(bytes(src, "utf8"))
    root = tree.root_node
    captures = RETURN_QUERY.captures(root)
    for node, _ in captures:
        if len(node.children) > 1:  # return value exists
            return True
    return False

# Optional: test function
if __name__ == "__main__":
    sample_code = '''
    /// <summary>
    /// This method adds two numbers.
    /// </summary>
    public int Add(int a, int b) {
        return a + b;
    }

    private void NotDocumented() {
        // no doc
    }
    '''
    tree = global_parser.parse(bytes(sample_code, "utf8"))
    funcs = get_fns_with_doc_comments(bytes(sample_code, "utf8"), tree)
    print(funcs[0] if funcs else "No functions found.")

    print("Has return value:", does_have_return(sample_code))