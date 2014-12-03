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
          return d.id
        };


    

    matrix.init = function(container){
      _svg = container
          .append("svg")
          .attr("height", height)
          .attr("width", width)
      // appending labels
      _svg
        .append("text")
        .text('concept example')
        .attr({
          x: 40,
          y: 100,
          'class': 'header'
        })

      _svg
        .append("text")
        .text('frequency')
        .attr({
          transform: 'translate(220, 100) rotate(-45)',
          'class': 'header'
        })

      _svg
        .append("text")
         .text('specificity')
        .attr({
          transform: 'translate(260, 100) rotate(-45)',
          'class': 'header'
        })
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
     /* _svg
        .selectAll(".block text")
        .attr('transform', function(d,i) {
          return 'matrix(' + [1, 0, 0, 1, offset.left, 0].join(' ') + ')';
        });
      */
    };

    /*
      enable update enter exit pattern
    */
    matrix.update = function(options){
      if(!_data.length)
        throw "matrix.update error. There aren't any data associated";
      console.log(_headers)
      // calculate local max and min
      var options = options || {
            measure: 'tf'
          },


          tf_min = options.bounds.min_tf,
          tf_max = options.bounds.max_tf,

          tfidf_min = options.bounds.min_tfidf,

          tfidf_max = options.bounds.max_tfidf,
          
          elements = _svg
            .selectAll('.block')
            .data(_data, _key),

          columns  = _svg
            .selectAll('.column')
            .data(_headers, function(d) {
              console.log('column', d)
              return d.name || d.G;
            });
      console.log(tf_min, tf_max, tfidf_min, tfidf_max)
      

      // cfr http://bost.ocks.org/mike/nest/
      matrix.draw(elements, columns, {
        tf_min: tf_min,
        tf_max: tf_max,
        tfidf_min: tfidf_min,
        tfidf_max: tfidf_max,
        measure: options.measure
      });
    };

    /*
      options.min and options.max
    */
    matrix.draw = function(elements, columns, options) {

      var offsetx     = 260,
          offsety     = 140,
          diffx       = 70,
          line_height = 28,

          tf_size = d3.scale.linear()
            .domain([options.tf_min, options.tf_max])
            .range([2,15]),

          tfidf_size = d3.scale.linear()
            .domain([options.tfidf_min, options.tfidf_max])
            .range([2,15]),

          update_selection = elements,
          enter_selection,
          switchers;

      // recalculate svg width according to the number of groups
      _svg.attr({
        width: offsetx +  diffx * (_headers.length + 1)
      })

      enter_selection = elements
        .enter()
          .append('g')
          .attr('class', function(d) {
            return 'block ' + (d.status || '');
          })
          .attr('cid', function(d) {
            return d.segment__cluster;
          }),
      
      // append background
      enter_selection
        .append('rect')
          .attr({
            y: -14,
            x: 20,
            height: line_height,
            width: offsetx - 40 +  diffx * (_headers.length + 1),
            fill: 'transparent'
          })
        

      

      // write column headers (text)
      columns.enter()
        .append('text')
          .attr({
            'class': 'header',
            transform: function(d,i){ return 'translate('+ (offsetx + diffx*(i+1))+' '+ (offsety - 40)+') rotate(-45)' ;},
          })
          .text(function(d,i){ return d.name})


        // set basic transform for each row (y)
        enter_selection
          .attr('transform', function(d,i) {
            return 'matrix(' + [1, 0, 0, 1, 0, i*26 + offsety].join(' ') + ')';
          });

        //
        // ADDING ELEMENTS LEFT TO RIGHT
        //
        // append base rectangle
        // switchers = enter_selection
        //   .append('g')
        //     .attr('class', 'switcher');
        // switchers
        //   .append('circle')
        //     .attr('class', 'toggler')
        //     .attr('cid', function(d) {
        //       return d.segment__cluster;
        //     })
        //     .attr('r', 8)
        //     .attr('cx', 10)
        //     .attr('cy', 0)


        // write text labels (they won't change)
        enter_selection
          .append('text')
            .attr({
              x: 40,
              y: 4
            })
            .text(function(d) {
              return d.segment__cluster || '...'
            });

        // adding tfrs
        enter_selection
          .append('circle')
            .attr({
              'class': 'tf',
              cx: offsetx -diffx/2,
              opacity: ".4",
              r: function(d) {
                return tf_size(+d.tf);
              }
            })

        enter_selection
          .append('circle')
            .attr({
              'class': 'tf_idf',
              cx: offsetx,
              opacity: ".4",
              r: function(d) {
                return tfidf_size(+d.tf_idf);
              }
            })


        // write column names


        // adding columns based on headers
        var cols_selection = enter_selection
          .selectAll('.measure')
            .data(function(d,i) {
              return _headers.map(function(o) { // put this function outside
                console.log('mappin', d, o.name)
                if(!d.cols)
                  return o;
                
                  for(var j=0; j<d.cols.length;j++) {
                    if(d.cols[j].G==o.name) {
                      //o.tf = d.cols[j].tf;
                      //o.tfidf = d.cols[j].tfidf;
                      return {
                        name: o.name,
                        id: d.cols[j].G,
                        tf: d.cols[j].tf,
                        tfidf: d.cols[j].tfidf
                      };
                    }
                  
                };
                // otherwise
                return o;
              });
            }, function(o){
              return o.name
            })


        cols_selection
          .exit()
          .remove()

        cols_selection
            .enter()
              .append('circle')
              .attr({
                'class'    : 'measure',
                'r'   : 1,
                'cy'        : -0.5,
                'gid'  : function(d) {return d.name},
                'cx'        : function(d,i) {return i*diffx + offsetx + diffx;}
              });

        

        update_selection
          .transition(500)
          .attr('transform', function(d,i) {
            return 'matrix(' + [1, 0, 0, 1, 0, i*26 + offsety].join(' ') + ')';
          })
          .attr('class', function(d) {
              return 'block ' + d.status;
            })
          .selectAll('.measure')
            .attr('r', function(d){
              
                if(options.measure == 'tf')
                  return tf_size(+d.tf||0)//*2;
                else
                  return tfidf_size(+d.tf_idf||0)//*2;
              })
            // .attr('cy', function(d){
            //     if(options.measure == 'tf')
            //       return -tf_size(+d.tf||0);
            //     else
            //       return -tfidf_size(+d.tf_idf||0);
            //   })
            

        update_selection
          .exit()
          .remove()
          
        return matrix;
      };

    return matrix;

  }; // end of timeline

  window.snark = snark;
})();