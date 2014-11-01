(function($, undefined){
  'use strict';

  var snark = window.snark || {};

  /*
    A 2d matrix chart to handle moulti column crossings.
    A reusable chart which is it not reusable, though.
    Handle with care.
    Usage type
    
    if(!timeline) {
      timeline = snark.timeline()
        .init(d3.select("#timeline"));
    };

    timeline
      .key(function(d){ console.log(d); return +d.key})
      .xValue(function(d){ console.log(d); return +d.key})
      .yValue(function(d){ console.log(d); return (+d.value)})
      .data(years)
      .update();
  */
  snark.matrix = function(){
    var matrix = {},
        width = 1000,
        height = 1352,
        margin = {top: 12, right: 12, bottom: 12, left: 12},

        _data = [],
        _headers = [],
        _svg, // the svg container
        
        _key = function(d){
          return d.cluster
        };


    

    matrix.init = function(container){
      _svg = container
          .append("svg")
          .attr("height", height)
          .attr("width", width)

      _svg
        .append("text")
        .text('GTF')
        .attr("x", 250)
        .attr("y", 26)

      return matrix;
    };

    matrix.data = function(v, k) {
      if (!arguments.length) return _data;
      _data = v;
      _key = k || _key;
      return matrix;
    };

    matrix.headers = function(v) {
      if (!arguments.length) return _headers;
      _headers = v;
      return matrix;
    };


    matrix.onscroll = function(offset) {
      _svg
        .selectAll(".block text")
        .attr('transform', function(d,i) {
          return 'matrix(' + [1, 0, 0, 1, offset.left, 0].join(' ') + ')';
        });
    };

    /*
      enable update enter exit pattern
    */
    matrix.update = function(options){
      if(!_data.length)
        throw "matrix.update error. There aren't any data associated";
      // calculate local max and min
      var options = options || {
            measure: 'tf'
          },

          local_min = d3.min(_data, function(d) {return d[options.measure]}),
          local_max = d3.max(_data,function(d) {return d[options.measure]}),
          
          elements = _svg
            .selectAll(".block")
            .data(_data, _key);
      
      // cfr http://bost.ocks.org/mike/nest/
      matrix.draw(elements, {
        min: local_min,
        max: local_max,
        measure: options.measure
      });
    };

    /*
      options.min and options.max
    */
    matrix.draw = function(elements, options) {
      console.log(options);
      
      var offsetx = 200,

          size = d3.scale.log()
            .base(Math.E)
            .domain([options.min, options.max])
            .range([2,18]),

        update_selection = elements,
        enter_selection = elements.enter()
          .append('g')
          .attr('class', function(d) {
            return 'block ' + d.status;
          }),
        switchers = enter_selection
          .append('g')
            .attr('class', 'switcher');

        // set basic transform for each row (y)
        enter_selection
          .attr('transform', function(d,i) {
            return 'matrix(' + [1, 0, 0, 1, 0, i*26 + 26*2].join(' ') + ')';
          });

        //
        // ADDING ELEMENTS LEFT TO RIGHT
        //
        // append base rectangle
        switchers
          .append('circle')
            .attr('class', 'toggler')
            .attr('cid', function(d) {
              return d.id;
            })
            .attr('r', 8)
            .attr('cx', 10)
            .attr('cy', 0)

        

        // write text labels (they won't change)
        enter_selection
          .append('text')
            .attr('x', 40)
            .text(function(d) {
              return d.cluster || '...'
            });

        // adding switchers
        

        

        // adding columns based on headers
        enter_selection
          .selectAll('rect')
            .data(function(d,i) {
              return _headers.map(function(o) { // put this function outside
                for(var j=0; j<d.tags.length;j++)
                  if(d.tags[j].id==o.id) {
                    //o.tf = d.tags[j].tf;
                    //o.tfidf = d.tags[j].tfidf;
                    return {
                      id: d.tags[j].id,
                      tf: d.tags[j].tf,
                      tfidf: d.tags[j].tfidf
                    };
                  }
                return o;
              });
            }, function(o){
              return o.id
            })
            .enter()
              .append('circle')
              .attr('class', 'measure')
              .attr('r', function(d){
                return d[options.measure]? Math.max(1, size(d[options.measure])):1;
              })
              .attr('cx', function(d,i) {
                return i*7 + offsetx;
              });


        update_selection
          .transition(500)
          .attr('transform', function(d,i) {
            return 'matrix(' + [1, 0, 0, 1, 0, i*26 + 26*2].join(' ') + ')';
          })
          .attr('class', function(d) {
              return 'block ' + d.status;
            })
          .selectAll('.measure')
            .attr('r', function(d){
                return d[options.measure]? Math.max(1, size(d[options.measure])):1;
              })
              .attr('cx', function(d,i) {
                return i*7 + offsetx;
              });

        update_selection
          .exit()
          .remove()
          

      return;


        
      // update row elements

      update_selection
        .selectAll(".block")
        .attr("y", function(d,i) {
          return i*26 + 26*2;
        });

      enter_selection
        .append("text")
        .text(function(d) {
          return d.content || '...'
        })
        .attr("y", function(d,i) {
          return i*26 + 26*2;
        })
        .style("fill", "#333333");
      

      update_selection
        .selectAll("circle.global")
        .transition()
          .duration(750)
          .attr("r", function(d){ return Math.max(1, size(d[options.measure]))})
          .attr("cx", 400)
          .attr("cy", function(d, i) {
            console.log('changing', i)
            return i*26 + 26*2;
          })
          //.style("fill", function(d){ return d[options.measure]==options.max?"rgb(25,158,154)":"#333333"})
      


      // draw circle (globals)
      enter_selection
        .append("circle")
        .attr("class", "global")
        .attr("fill-opacity", .3)
        .attr("r", function(d){return Math.max(1, size(d[options.measure]))})
        .attr("class", "circle")
        .attr("cx", 400)
        .attr("cy", function(d, i) {
          return i*26 + 26*2;
        })

      update_selection
        .exit()
        .remove()


      // for each actor. calculate actor max et actor min
      for(var i=0; i< Math.min(_headers.length, 50); i++) {
        var column_id = _headers[i].id,
            radius = function(d){ 
          var match = d.tags.filter(function(j){
            return j.id == column_id
          });
          try{
            //if(match.length)
              //console.log(match, options.measure , match[0][options.measure])
            return match.length? Math.max(2, size(match[0][options.measure])): 1
          } catch(err) {
            console.log(d, 'has error', err)
            return 1;
          }
        };
        
        /*update_selection
          .selectAll("circle.tag")
          .transition()
          .duration(750)
          .attr("r", radius)
          */
        
        enter_selection
          .append("circle")
          .attr("class", "tag  "+ column_id)
          //.style("fill", "#333333")
          .attr("fill-opacity", .4)
          .attr("r", radius)
          
          .attr("cx", 400 + (i+1)*20)
          .attr("cy", function(d, j) {
            return j*26 + 26*2;
          })
        //_data[0].tags[i][options.measure]
        
      }
      

    };

    return matrix;

  }; // end of timeline

  window.snark = snark;
})();