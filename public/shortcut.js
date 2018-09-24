/*
 * Copyright 2018 Carnegie Mellon University
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

function ShortcutManager()
{
    var me = this;

    this.disabled = false;
    this.shortcuts = {};
    
    this.addshortcut = function(key, callback) {
        if (typeof key === 'number') {
            key = [key];
        }
        for (i in key) {
            if (!(key[i] in this.shortcuts)) {
                this.shortcuts[key[i]] = [];
            }
            this.shortcuts[key[i]].push(callback);
        }
    }

    $(window).keydown(function(e) {
//        console.log("Key press: " + e.keyCode);
        var keycode = e.keyCode ? e.keyCode : e.which;
//        eventlog("keyboard", "Key press: " + keycode);
        if (keycode in me.shortcuts) {
            event.preventDefault();
            for (var i in me.shortcuts[keycode]) {
                me.shortcuts[keycode][i]();
            }
        }
    });

}
