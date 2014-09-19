'use strict';

/**
 * @ngdoc filter
 * @name svenClientApp.filter:tag
 * @function
 * @description
 * # tag
 * Filter in the svenClientApp.
 */
angular.module('svenClientApp')
  .filter('tag', function () {
    return function (input) {
      return input.split(' - ').shift();
    };
  });
