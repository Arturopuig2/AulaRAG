const fs = require('fs');

// We can just simulate the exact logic.
let text = "<p>[CORRECTO] Muy bien. La palabra es aguda.</p>";
let formattedText = text;
const correctoRegex = /\[CORRECTO\]/gi;
let foundStatus = null;
if (formattedText.match(correctoRegex)) {
    console.log("Matched correcto!");
    formattedText = formattedText.replace(correctoRegex, '').trim();
    foundStatus = "correct";
}
console.log("Result:", formattedText);
