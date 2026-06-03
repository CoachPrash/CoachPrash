import { basicSetup, EditorView } from 'codemirror';
import { java } from '@codemirror/lang-java';
import { oneDark } from '@codemirror/theme-one-dark';
import { keymap } from '@codemirror/view';

/**
 * Initialize a CodeMirror 6 editor for Java code.
 *
 * @param {HTMLElement} container - DOM element to mount the editor in
 * @param {string} starterCode - Initial code content
 * @param {object} options - { onRunCode, dark }
 * @returns {EditorView} The editor instance
 */
export function initCodeEditor(container, starterCode, options = {}) {
    var extensions = [
        basicSetup,
        java(),
        EditorView.lineWrapping,
    ];

    // Dark theme (matches site dark mode if enabled)
    if (options.dark) {
        extensions.push(oneDark);
    }

    // Ctrl+Enter / Cmd+Enter to run code
    if (options.onRunCode) {
        extensions.push(keymap.of([{
            key: 'Mod-Enter',
            run: function () {
                options.onRunCode();
                return true;
            },
        }]));
    }

    var editor = new EditorView({
        doc: starterCode || '',
        extensions: extensions,
        parent: container,
    });

    return editor;
}

/**
 * Get the current code from an editor instance.
 */
export function getEditorCode(editor) {
    return editor.state.doc.toString();
}

/**
 * Replace all code in the editor.
 */
export function setEditorCode(editor, code) {
    editor.dispatch({
        changes: {
            from: 0,
            to: editor.state.doc.length,
            insert: code,
        },
    });
}
