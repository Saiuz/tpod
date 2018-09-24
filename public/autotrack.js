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

function AutoTracker(job, tracks) {
    this.fulltracker = null;
    this.job = job;
    this.tracks = tracks;

    this.full = function(callback) {
	    // Disable interaction
        if (this.fulltracker) {
            server_request("trackfull", [this.job.jobid, this.fulltracker], function(data) {
                console.log("Successful tracked object");
                callback(data);
            });
        } else {
            alert("Please select a full tracking algorithm");
            callback();
        }
    }
}
