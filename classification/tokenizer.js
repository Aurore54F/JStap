// Copyright (C) 2019 Aurore Fass
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.

// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

// Lexical analysis of a file whose path is given as command line argument. Esprima is used for the
// tokenizing process and prints in stdout the list of lexical units (tokens) present in the file.

var fs = require("fs");
var esprima = require('esprima');


function tokenize(js, value) {
	var text = fs.readFileSync(js).toString('utf-8');
	esprima.tokenize(text, {comment: true}, function (node) {
		console.log(node.type);
		if (value === '1') {
                        console.log('###aaa@@@###qqq');
			console.log(node.value);
                        console.log('###aaa@@@###qqq');
		}
	});
}


tokenize(process.argv[2], process.argv[3]);
