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

function Job(data)
{
    var me = this;

    this.slug = null;
    this.start = null;
    this.stop = null; 
    this.width = null; 
    this.height = null; 
    this.skip = null; 
    this.perobject = null;
    this.completion = null;
    this.blowradius = null;
    this.thisid = null;
    this.labels = null;
    this.homography = null;
    this.topimageurl = null;
    this.nextid = null;
    this.onlinetrackers = [];
    this.bidirectionaltrackers = [];
    this.multiobjecttrackers = [];
    this.pointmode = null;

    this.frameurl = function(i)
    {
        folder1 = parseInt(Math.floor(i / 100));
        folder2 = parseInt(Math.floor(i / 10000));
        return "frames/" + me.slug + 
            "/" + folder2 + "/" + folder1 + "/" + parseInt(i) + ".jpg";
    }
}

function job_import(data)
{
    var job = new Job();
    job.slug = data["slug"];
    job.start = parseInt(data["start"]);
    job.stop = parseInt(data["stop"]);
    job.width = parseInt(data["width"]);
    job.height = parseInt(data["height"]);
    job.skip = parseInt(data["skip"]);
    job.perobject = parseFloat(data["perobject"]);
    job.completion = parseFloat(data["completion"]);
    job.blowradius = parseInt(data["blowradius"]);
    job.jobid = parseInt(data["jobid"]);
    job.labels = data["labels"];
    job.attributes = data["attributes"];
    job.training = parseInt(data["training"]);
    job.homography = data["homography"]
    job.topimageurl = "homographies/" + job.slug + "/topview.jpg";
    job.onlinetrackers = data["trackers"]["online"];
    job.bidirectionaltrackers = data["trackers"]["bidirectional"];
    job.multiobjecttrackers = data["trackers"]["multiobject"];
    job.nextid = parseInt(data["nextid"]);
    job.pointmode = parseInt(data["pointmode"]) ? true : false;

    console.log("Job configured!");
    console.log("  Blow Radius: " + job.blowradius);
    console.log("  Slug: " + job.slug);
    console.log("  Start: " + job.start);
    console.log("  Stop: " + job.stop);
    console.log("  Width: " + job.width);
    console.log("  Height: " + job.height);
    console.log("  Skip: " + job.skip);
    console.log("  Per Object: " + job.perobject);
    console.log("  Training: " + job.training);
    console.log("  Job ID: " + job.jobid);
    console.log("  Labels: ");
    for (var i in job.labels)
    {
        console.log("    " + i + " = " + job.labels[i]);
    }
    console.log("  Attributes:");
    for (var i in job.attributes)
    {
        for (var j in job.attributes[i])
        {
            console.log("    " + job.labels[i] + " = " + job.attributes[i][j])
        }
    }

    return job;
}
